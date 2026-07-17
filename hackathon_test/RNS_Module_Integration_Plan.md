# Supervised_RNS_dMRI → OpenRecon Module Integration Plan

Working plan for integrating [Supervised_RNS_dMRI](https://github.com/Bradley-Karat/Supervised_RNS_dMRI)
(diffusion MRI model fitting via Realistic Noise Synthesis) into a new
Open Recon module (`supervised_rns_dmri`).

> Contains architectural decisions and sequencing for the hackathon exercise.
> Decide before sharing whether this should ship to students as-is (reference
> solution) or be excluded so `supervised_rns_dmri` remains their own exercise.

## The plan

1. **Test the RNS installation in the devcontainer** — a throwaway script confirming `import Supervised_RNS_dMRI` / `import diffsimgen` work. ✅ Done.

2. **Prepare the datasets, in original format with auxiliary files (bval/bvec)**
   Split into two categories, not one:
   - a **training set** — used once, offline, outside the module, to produce the two pickle files (e.g. `trained_rf.pkl`, `modelinfo.pkl`)
   - a small **inference/test set** — one subject's `dwi.nii.gz` + `.bval`/`.bvec` + brain mask + noisemap, which is all the *live* module will ever see
   Keep the training set tiny — pipeline correctness matters more than model accuracy this week.

3. **Create a script to move everything into h5 format** — the real design decision, not just a format conversion.
   MRD has no native field for bval/bvec/mask/noisemap (no DICOM-style custom tag equivalent built in). Decide one of:
   - N `ismrmrd.Image`s (one per DWI volume) + bval/bvec smuggled per-image via `userParameterLong`/`Double`, or
   - one 4D blob (nibabel-style) + a JSON sidecar passed through `ui_data`
   Whichever is picked here is what both this conversion script and the module's parsing logic (step 6) must agree on.

   🟡 In progress — found an existing converter, `server/nifti2mrd.py` (adapted from the
   [open-recon-fetal-brain-measurements](https://github.com/jlautman1/open-recon-fetal-brain-measurements)
   project), and confirmed it runs end-to-end:
   ```bash
   cd server
   python3 nifti2mrd.py -i ../test/hackathon_data/test.nii.gz -o ../test/hackathon_data/test.h5
   ```
   Verified working against `test/hackathon_data/test.nii.gz`, producing `test/hackathon_data/test.h5`.

   What it does: loads a NIfTI volume with `nibabel`, extracts position/orientation from the
   affine matrix (RAS→LPS conversion), writes one `ismrmrd.Image` per slice into a proper
   ISMRMRD `Dataset`, and carries filename-derived + orientation metadata via `ismrmrd.Meta`.

   What it does **not** yet handle — still the open item for this step:
   - Only takes a single 3D volume (`if len(data.shape) == 4: data = data[:, :, :, 0]  # Take first volume`) — a 4D DWI series would need every volume converted, not just the first.
   - No bval/bvec/mask/noisemap ingestion at all — it has no notion of these files, so the core step-3 decision (per-image `userParameterLong`/`Double` vs. 4D blob + JSON sidecar) is still unresolved.
   - Next: either extend `nifti2mrd.py` to loop over the 4th (diffusion) dimension and attach bval/bvec per volume, or write a separate DWI-specific converter that calls into this one per-volume once the encoding scheme is picked.

   🟡 Second converter found for the reverse leg: [mrd2nii](https://github.com/shimming-toolbox/mrd2nii)
   (ISMRMRD → NIfTI, BIDS-compliant sidecar). Verified via source inspection (not yet installed/tested
   in the devcontainer):
   - **Not a C/C++ compile step** — pure Python (`setuptools.build_meta`), only real dependency is
     `ismrmrd==1.14.1` (a `py3-none-any` wheel already used elsewhere in this repo). It just isn't
     published on PyPI, so install the same way as `Supervised_RNS_dMRI`:
     `pip install git+https://github.com/shimming-toolbox/mrd2nii.git`. One-line Dockerfile addition,
     no new build tooling.
   - **Fully embeddable, no mandatory disk writes**: `mrd2nii.mrd2nii_main.mrd2nii_volume(metadata, volume_images, skip_sidecar=False)`
     takes an already-parsed `ismrmrd.xsd` header + a list of `ismrmrd.Image` objects (exactly what
     `process()` already has as `mrd_header` / `img_group`) and returns a nibabel image **in memory**
     — the file-writing CLI (`mrd2nii_dset`) is just a thin wrapper around this. No temp files needed
     for the ISMRMRD → NIfTI leg.
   - The reverse leg (NIfTI → ISMRMRD, i.e. `nifti2mrd.py`) is *not* embeddable yet — `convert_nifti_to_ismrmrd()`
     hard-requires a file path (`nib.load(nifti_path)`). Since this file is ours, not a third-party
     dependency, the fix is small: split off an inner function that accepts an already-loaded
     `nib.Nifti1Image` object directly, keeping the path-based version as a thin CLI wrapper.
   - **Bonus lead on the bval/bvec question**: `mrd2nii_volume` groups slices into a 4D volume using
     each image's native `repetition` header field, and `ismrmrd.Image` headers already carry native
     `user_int[8]` / `user_float[8]` arrays (no `Meta`/`userParameterLong` needed). Tagging each DWI
     volume with a `repetition` index and its b-value/b-vector in `user_float` would give 4D
     reconstruction *and* diffusion encoding for free from fields mrd2nii already reads — worth
     evaluating against the JSON-sidecar option before finalizing the step-3 encoding scheme.

   **Revised step-3 pipeline** (client sends ISMRMRD in, live module path, no intermediate files):
   ```
   client → ISMRMRD (socket, MRD_MESSAGE_ISMRMRD_IMAGE)
          → mrd2nii_volume(mrd_header, img_group)         # in-memory, ISMRMRD → NIfTI
          → Supervised_RNS_dMRI inference-only entry point # step 4
          → convert_nifti_to_ismrmrd(nii_image, ...)       # in-memory, NIfTI → ISMRMRD (needs the small refactor above)
          → client (send_image())
   ```
   Decision: retain both converters' conversion *logic* (don't hand-roll a third implementation) but
   call their importable functions directly rather than shelling out to their CLIs or writing files
   to disk at each hop — the right trade-off for hackathon time constraints, and both tools turn out
   to already be (or trivially become) in-memory-friendly.

4. **Test on data with a script that handles the data format and auxiliary info** ✅ Dry-run validated.
   `server/test_RSN.py` builds `sys.argv` by hand and calls `Supervised_RNS_dMRI.run.main()` directly
   (see step-2/CLI notes elsewhere in this doc). Two bugs fixed to get a clean dry-run against
   `hackathon_test/data/sub-06400_*`:
   - `sys.argv` entries must be one shell "word" each — `"--path-dwi /path/to/file"` as a single
     combined string is not the same as two separate list elements `"--path-dwi", "/path/to/file"`;
     argparse silently misparses the combined form and Snakemake tries to `open()` the whole string
     as a config file path.
   - `--path-dwi` (the only path-override flag the toolbox exposes — there is no separate flag for
     bval/bvec/mask/noisemap) requires a wildcard, e.g. `sub-{subject}_dwi.nii.gz`, not a literal
     path — snakebids needs the wildcard to enumerate subjects. bval/bvec/mask/noisemap are then
     auto-discovered as sibling files sharing the dwi file's prefix (`sub-06400_dwi.bval`,
     `sub-06400_brain_mask.nii.gz`, etc.) — which is exactly how `hackathon_test/data/` is already
     named, no BIDS `sub-X/dwi/` subfolder needed for this single-subject override path.

   With both fixed, `python3 test_RSN.py` (dry-run, `-np`) resolves subject `06400` and produces a
   clean 5-job DAG: `make_noisemap` → `setup_and_train_model` (checkpoint) → `apply_model` →
   `collect_done` → `all`.

   **This confirms there is no CLI/argparse-level "inference only" flag** — every run through
   `Supervised_RNS_dMRI.run.main()` includes `setup_and_train_model`, i.e. it always retrains from
   whatever subject data it's pointed at. Getting an inference-only path for the live module means
   calling an internal Python function directly, bypassing this Snakemake driver entirely — see
   step 6, which now has a confirmed candidate function.

5. **Create a new module** (see `AGENTS.md` → "Adding a New Module", and `.github/agents/new-module.agent.md`). ✅ Scaffolded.
   The agent's 6 steps map onto this plan:

   | new-module agent step | This plan | Status |
   |---|---|---|
   | 1. Choose workflow type | — | i2i-style (pre-reconstructed DWI images in, parametric maps out) — not r2ci, no raw k-space involved |
   | 2. Create module directory | step 5 | Done — `server/modules/supervised_rns_dmri/` |
   | 3. Implement `process()` | step 6 | Pending — currently a smoke-tested pass-through |
   | 4. Configure `appl_spec.json` | step 5 | Placeholder params (`modelId`, `deltaId`, `smallDeltaId`) mirroring the toolbox's `--Model`/`--Delta`/`--Small_Delta` CLI flags |
   | 5. Register + test | step 7 | Registered in `server.py`; pass-through verified via client/server |
   | 6. Update docs | — | `AGENTS.md`, `server/Readme.md`, module `Readme.md` updated. Root `Readme.md` intentionally left untouched — it documents the generic tutorial flow, not this hackathon-specific module |

6. **Integrate the prototype script into the new module** 🟡 Scaffolded, logic still TODO.
   Split across two files rather than crammed into one, so each stage is independently testable
   with plain arrays/objects (no MRD server needed) the same way `test_RSN.py` already validates
   the toolbox standalone:

   - **`supervised_rns_dmri.py`** stays MRD-protocol-only. `_process_image_impl()` becomes a thin
     orchestrator:
     ```python
     def _process_image_impl(img_group, ui_data, mrd_header):
         dwi_nii = rns_inference.mrd_to_nifti(img_group, mrd_header)
         bval, mask_nii = rns_inference.extract_dwi_aux(img_group, ui_data)
         result_niis = rns_inference.run_inference(dwi_nii, bval, mask_nii)
         return rns_inference.nifti_to_mrd_images(result_niis, img_group)
     ```
   - **`rns_inference.py`** (new adapter module) — all toolbox-specific logic, four functions:
     | Function | Does | Status |
     |---|---|---|
     | `mrd_to_nifti(img_group, mrd_header)` | Calls `mrd2nii.mrd2nii_main.mrd2nii_volume()` directly — already in-memory | Depends on mrd2nii being installed (see step 3) |
     | `extract_dwi_aux(img_group, ui_data)` | Pulls bval/bvec/mask out of the MRD stream | Blocked on the still-open step-3 encoding decision |
     | `run_inference(dwi_nii, bval, mask_nii)` | Ports the ~30 reusable lines of `run_model_fitting.py` (masking/reshaping, SANDI direction-averaging, `fneurite`/`fsoma`/`fextra` derivation) around the one genuinely reusable call: `apply_RF_python(signal, trainedML, log)` — confirmed pure (numpy array + unpickled model dict in, numpy array out, no Snakemake coupling). `run_model_fitting.py` itself is *not* importable — it's a Snakemake `script:` block driven by a magic `snakemake` object, so it's the reference implementation to port, not a library to call. Load `trained_rf.pkl`/`modelinfo.pkl` once, cached at module level, not per-request. | Candidate function confirmed (step 4); upstream direction-averaging step (`SphericalMeanFromSH.py`/`llsFitSH.py`) not yet inspected |
     | `nifti_to_mrd_images(result_niis, img_group)` | Small refactor of `nifti2mrd.py`'s `convert_nifti_to_ismrmrd()` to accept an in-memory `nib.Nifti1Image` instead of requiring a file path | Not started |

   Net effect: the only disk I/O in the live request path is the one-time model pickle load — every
   other stage is array/object in, array/object out.

7. **Test at the devcontainer level (client/server)**
   ```bash
   # Terminal 1
   cd server && ./run_server.sh supervised_rns_dmri
   # Terminal 2
   cd client && ./run_client.sh supervised_rns_dmri && python3 display.py out.h5
   ```
   ✅ Pass-through path verified working end-to-end. Re-run once step 6 replaces the stub with real logic.

## Open decisions blocking step 6

- bval/bvec/mask/noisemap → MRD encoding scheme (step 3)
- ~~confirmed inference-only entry point in the toolbox (step 4)~~ ✅ `apply_RF_python(signal, trainedML, log)` confirmed reusable; still need to inspect the SANDI direction-averaging step upstream of it (`SphericalMeanFromSH.py`/`llsFitSH.py`)
- whether this module ships in the students' copy of the repo, or stays a private reference implementation
