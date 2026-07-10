# r2ci_bart — Raw k-space to Complex-Image Reconstruction with BART

## Overview

This module implements the **Raw-to-Complex-Image (r2ci)** Open Recon pipeline.
It receives raw k-space acquisitions from the scanner, buffers them per slice, estimates coil sensitivities, and reconstructs using
[BART](https://mrirecon.github.io/bart)'s iterative SENSE / compressed sensing toolchain (`ecalib` + `pics`).

**This is the main module to modify when building a custom BART reconstruction with this python-based server.**

## Files

| File | Description |
|---|---|
| `r2ci_bart.py` | Module entry point and reconstruction pipeline |
| `doc/appl_spec.json` | Open Recon application specification (UI parameters, metadata) |
| `doc/appl_spec_schema.json` | JSON schema for validating `appl_spec.json` |
| `doc/application_guide.md` | Scanner-facing application guide (device description) |

## Processing Pipeline

```
Raw k-space acquisitions (MRD Acquisition messages)
    │
    ▼
Buffer readouts per slice  →  [cha × PE × RO × phase]
    (triggered by ACQ_LAST_IN_SLICE flag)
    │
    ▼
─── BART section (edit here) ──────────────────────────────────
│  sens = bart('ecalib -m 1', kspace)                         │
│  reco = bart('pics -e -S',  kspace, sens)                   │
────────────────────────────────────────────────────────────────
    │
    ▼
Scale, format as MRD Image
    │
    ▼
Send complex image back to client (MRD Image message)
```

Slicing is handled correctly for **single-slice**, **multi-slice**, and
**segmented / interleaved** acquisitions via the `_slice_group_key()` function,
which groups readouts by `(slice, repetition, contrast, average, set)`.

## Scanner UI Parameters

Defined in `doc/appl_spec.json` and accessible via `ui_data` at runtime:

| Parameter ID | Type | Default | Description |
|---|---|---|---|
| `numCoilIntId` | `int` | `-1` | Number of coils for reconstruction. `-1` = use all available coils. |
| `picsFlagsId` | `string` | `"-e -S"` | Flags passed verbatim to BART's `pics` command. |

Example: setting `picsFlagsId` to `"-e -S -l1 -r 0.001"` adds $\ell_1$-wavelet regularization.

## How to Add Your Own BART Reconstruction

1. Open `r2ci_bart.py` and locate the **BART section** inside `process_raw()`.
2. Replace or extend the `ecalib` / `pics` calls with your own BART commands.
3. Optionally add new UI parameters in `doc/appl_spec.json` and read them via
   `mrdhelper.get_json_param(ui_data, 'yourParamId')`.
4. Test existing tests locally:

```bash
# Terminal 1
cd server
./run_server.sh r2ci_bart

# Terminal 2
cd client
./run_client.sh        # sends test data, writes out.h5
python3 display.py out.h5
```

5. Run the automated test suite:

```bash
cd test
./test_server.sh --mode r2ci_bart
```

6. Add your own application-specific test by appending an entry to `test/tests.sh`:

```bash
# Format: <error-margin> <OR-mode> <data> <ref-reco> <speed: fast|slow>
"1e-6 r2ci_bart my_data.h5 my_ref_reco.h5 fast"
```

   - Place your raw input data in `test/data/my_data.h5`.
   - Generate a reference reconstruction (e.g. by running the server once and copying `client/out.h5`) and save it as `test/ref/my_ref_reco.h5`.
   - The test runner computes the NRMSE between the server output and the reference; it passes when NRMSE ≤ `error-margin`.
   - Mark the test `slow` if it takes more than a few seconds (e.g. large matrix, many slices, or heavy regularization).

## Running in Docker

```bash
cd server
./run_docker.sh r2ci_bart
```

The Docker image bundles BART, sets `BART_TOOLBOX_PATH`, and exposes port `9002`.
See `server/Dockerfile` and `server/docker_build.sh` for details.

## Data Flow (MRD message types)

| Direction | MRD Message | Content |
|---|---|---|
| Scanner → Server | `MRD_MESSAGE_ISMRMRD_ACQUISITION` | Raw k-space readout + header |
| Server → Scanner | `MRD_MESSAGE_ISMRMRD_IMAGE` | Reconstructed complex image |

The Open Recon platform is configured via `"emitter": "raw"` and
`"injector": "compleximage"` in `doc/appl_spec.json`.

## Debug Output

Intermediate arrays are saved to `/tmp/share/debug/` (raw k-space `raw.npy`, sensitivity maps `sens.npy`, reconstruction output `reco.npy`) when the folder exists. To enable debug output:

```bash
mkdir -p /tmp/share/debug/
```
