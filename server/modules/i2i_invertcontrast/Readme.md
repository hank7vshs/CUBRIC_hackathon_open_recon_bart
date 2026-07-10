# i2i_invertcontrast — Image-to-Image Contrast Inversion

## Overview

This module implements the **Image-to-Image (i2i)** Open Recon pipeline.
It receives reconstructed magnitude images directly from the scanner's
inline reconstruction (ICE), inverts their contrast, and returns the result.

It is the **simplest possible Open Recon module** and is designed as a
minimal starting template for image-to-image workflows.

## Files

| File | Description |
|---|---|
| `i2i_invertcontrast.py` | Module entry point and contrast inversion logic |
| `doc/appl_spec.json` | Open Recon application specification (UI parameters, metadata) |
| `doc/appl_spec_schema.json` | JSON schema for validating `appl_spec.json` |
| `doc/application_guide.md` | Scanner-facing application guide (device description) |

## Processing Pipeline

```
Reconstructed magnitude images (MRD Image messages)
    │
    ▼
Accumulate images per series
    │
    ▼
─── Processing (edit here) ───────────────────────────────────────────
│  maxVal = 2^BitsStored − 1   (e.g. 4095 for 12-bit images)  │
│  output = maxVal − input                                     │
──────────────────────────────────────────────────────────────────
    │
    ├─ sendOriginalBoolId = true ──► return original images instead
    │
    ▼
Send contrast-inverted image back to client (MRD Image message)
```

## Scanner UI Parameters

Defined in `doc/appl_spec.json` and accessible via `ui_data` at runtime:

| Parameter ID | Type | Default | Description |
|---|---|---|---|
| `sendOriginalBoolId` | `bool` | `false` | If enabled, the unmodified input image is returned **instead of** the contrast-inverted result. |

The contrast inversion formula itself is fully determined by the image's bit depth, which is read from the MRD image header automatically.

## How to Adapt This Module

`i2i_invertcontrast.py` is structured as a template:

1. The `process_image()` function receives a list of `ismrmrd.Image` objects for a complete series and returns a list of processed images.
2. Replace the inversion formula with your own per-image computation.
3. Test locally:

```bash
# Terminal 1
cd server
./run_server.sh i2i_invertcontrast

# Terminal 2
cd client
python3 client.py ../test/data/tse_i2i.h5
python3 display.py out.h5
```

4. Run the automated test suite:

```bash
cd test
./test_server.sh --mode i2i_invertcontrast
```

5. Add your own application-specific test by appending an entry to `test/tests.sh`:

```bash
# Format: <error-margin> <OR-mode> <data> <ref-reco> <speed: fast|slow> [<ui-data>]
"1e-6 i2i_invertcontrast my_images.h5 my_ref_reco.h5 fast"
```

   - Place your input images in `test/data/my_images.h5`.
   - Generate a reference output (e.g. by running the server once and
     copying `client/out.h5`) and save it as `test/ref/my_ref_reco.h5`.
   - The test runner computes the NRMSE between the server output and the reference; it passes when NRMSE ≤ `error-margin`.

## Running in Docker

```bash
cd server
./run_docker.sh i2i_invertcontrast
```

## Data Flow (MRD message types)

| Direction | MRD Message | Content |
|---|---|---|
| Scanner → Server | `MRD_MESSAGE_ISMRMRD_IMAGE` | Reconstructed magnitude image |
| Server → Scanner | `MRD_MESSAGE_ISMRMRD_IMAGE` | Contrast-inverted image |

The Open Recon platform is configured via `"emitter": "image"` and
`"injector": "image"` in `doc/appl_spec.json`.

## Debug Output

Intermediate images are saved to `/tmp/share/debug/` as `.npy` files when the folder exists.
