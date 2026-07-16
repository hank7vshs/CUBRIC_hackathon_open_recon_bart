# supervised_rns_dmri — Diffusion MRI Model Fitting via Realistic Noise Synthesis

## Overview

This module implements the **Image-to-Image (i2i)** Open Recon pipeline.
It receives reconstructed DWI magnitude images directly from the scanner's
inline reconstruction (ICE) and fits a diffusion model using a machine
learning model trained offline with
[Supervised_RNS_dMRI](https://github.com/Bradley-Karat/Supervised_RNS_dMRI).

**Status: scaffold.** `process()` currently passes images through
unmodified. See the TODOs in `_process_image_impl()` in
`supervised_rns_dmri.py` for the remaining implementation steps.

## Files

| File | Description |
|---|---|
| `supervised_rns_dmri.py` | Module entry point and model-fitting logic |
| `doc/appl_spec.json` | Open Recon application specification (UI parameters, metadata) |
| `doc/appl_spec_schema.json` | JSON schema for validating `appl_spec.json` |
| `doc/application_guide.md` | Scanner-facing application guide (device description) |

## Processing Pipeline (target design)

```
Reconstructed DWI magnitude images (MRD Image messages)
    │
    ▼
Accumulate images per series
    │
    ▼
─── Processing (not yet implemented) ─────────────────────────────────
│  1. Read bval/bvec/brain-mask/noisemap (encoding TBD)                │
│  2. Assemble 4D DWI volume from the image group                      │
│  3. Load pre-trained model artifacts from model/                     │
│  4. Run inference-only entry point from Supervised_RNS_dMRI          │
│  5. Convert resulting parametric map(s) to MRD Images                │
────────────────────────────────────────────────────────────────────
    │
    ▼
Send parametric map image(s) back to client (MRD Image message)
```

## Scanner UI Parameters

Defined in `doc/appl_spec.json` and accessible via `ui_data` at runtime.
These mirror the CLI flags of the `Supervised_RNS_dMRI` toolbox and are
placeholders pending the real pipeline implementation:

| Parameter ID | Type | Default | Description |
|---|---|---|---|
| `modelId` | `string` | `SANDI` | Diffusion model to fit (`--Model`) |
| `deltaId` | `double` | `23.6` | Diffusion gradient separation time in ms (`--Delta`) |
| `smallDeltaId` | `double` | `7.0` | Diffusion gradient duration in ms (`--Small_Delta`) |

## How to Adapt This Module

`supervised_rns_dmri.py` is structured like `i2i_invertcontrast.py`:

1. The `process_image()` function receives a list of `ismrmrd.Image` objects for a complete series and returns a list of processed images.
2. Replace the pass-through body of `_process_image_impl()` with the model-fitting pipeline (see the numbered TODOs in that function).
3. Test locally:

```bash
# Terminal 1
cd server
./run_server.sh supervised_rns_dmri

# Terminal 2
cd client
python3 client.py <path-to-test-data>.h5
python3 display.py out.h5
```

4. Run the automated test suite once a test dataset and reference output exist:

```bash
cd test
./test_server.sh --mode supervised_rns_dmri
```

5. Add your own application-specific test by appending an entry to `test/tests.sh`:

```bash
# Format: <error-margin> <OR-mode> <data> <ref-reco> <speed: fast|slow> [<ui-data>]
"1e-6 supervised_rns_dmri my_dwi.h5 my_ref_reco.h5 fast"
```

## Running in Docker

```bash
cd server
./run_docker.sh supervised_rns_dmri
```

## Data Flow (MRD message types)

| Direction | MRD Message | Content |
|---|---|---|
| Scanner → Server | `MRD_MESSAGE_ISMRMRD_IMAGE` | Reconstructed DWI magnitude images |
| Server → Scanner | `MRD_MESSAGE_ISMRMRD_IMAGE` | Fitted parametric map image(s) |

The Open Recon platform is configured via `"emitter": "image"` and
`"injector": "image"` in `doc/appl_spec.json`.

## Debug Output

Intermediate images are saved to `/tmp/share/debug/` as `.npy` files when the folder exists.
