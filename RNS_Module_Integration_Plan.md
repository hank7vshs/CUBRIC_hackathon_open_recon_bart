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

4. **Test on data with a script that handles the data format and auxiliary info**
   This script must call only the **inference/apply** path of the toolbox, not the full `process_all_datasets` → `train_machine_learning_model` → `analyze_all_datasets` pipeline — training offline only, per step 2. Confirm which function in `apply_RF_python.py` / `run_model_fitting.py` is the inference-only entry point before writing this script, since it gets lifted directly into the module in step 6.

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

6. **Integrate the prototype script into the new module**
   Replace the pass-through body of `_process_image_impl()` in `server/modules/supervised_rns_dmri/supervised_rns_dmri.py` with the working logic from step 4.

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
- confirmed inference-only entry point in the toolbox (step 4)
- whether this module ships in the students' copy of the repo, or stays a private reference implementation
