# Converting Siemens Raw Data (.dat) to ISMRMRD (.h5)

- [Converting Siemens Raw Data (.dat) to ISMRMRD (.h5)](#converting-siemens-raw-data-dat-to-ismrmrd-h5)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Step-by-Step Guide](#step-by-step-guide)
    - [Step 1: Obtain a .dat file](#step-1-obtain-a-dat-file)
    - [Step 2: Identify the correct measurement](#step-2-identify-the-correct-measurement)
    - [Step 3: Convert to ISMRMRD HDF5](#step-3-convert-to-ismrmrd-hdf5)
    - [Step 4: Reconstruct with Open Recon](#step-4-reconstruct-with-open-recon)
    - [Step 5: View the result](#step-5-view-the-result)
  - [Understanding Multi-Measurement Files](#understanding-multi-measurement-files)
  - [Troubleshooting](#troubleshooting)
    - [All acquisitions flagged as noise](#all-acquisitions-flagged-as-noise)
    - [Shape mismatch during reconstruction](#shape-mismatch-during-reconstruction)
    - [siemens\_to\_ismrmrd not found](#siemens_to_ismrmrd-not-found)
    - [No images returned by the server](#no-images-returned-by-the-server)
  - [Background: What the Conversion Does](#background-what-the-conversion-does)

## Overview

Siemens MRI scanners store raw k-space data in a proprietary `.dat` format. To process this data with the Open Recon server, it needs to be converted to the [ISMRMRD](https://ismrmrd.github.io/) format (stored as HDF5 `.h5` files).

This guide walks through converting your own Siemens `.dat` files and reconstructing them with the `r2ci_bart` module.

## Prerequisites

- The devcontainer must be running (it includes `siemens_to_ismrmrd` and all dependencies).
- A Siemens `.dat` raw data file exported from the scanner.

Both tools (`siemens_to_ismrmrd` and the ISMRMRD library) are installed automatically by the devcontainer Dockerfile.

## Quick Start

The included script handles conversion with built-in validation:

```bash
cd further_materials/04_raw_data_conversion

# Convert measurement 2 (the actual scan, not calibration data)
./convert_dat_to_h5.sh gre_sphere.dat 2
```

Then reconstruct:

```bash
# Terminal 1: start the server
cd server && ./run_server.sh r2ci_bart

# Terminal 2: send the converted file
cd client && python3 client.py ../further_materials/04_raw_data_conversion/gre_sphere.h5
python3 display.py out.h5
```

## Step-by-Step Guide

### Step 1: Obtain a .dat file

Export raw data from the Siemens `twix` tool as single raid file. The file will have a name like:
```
meas_MIDxxxxx_FIDxxxxxx_gre.dat
```

Copy it into the workspace of this tutorial. It includes an example file `gre_sphere.dat` in this directory that you can use to follow along.

### Step 2: Identify the correct measurement

Siemens `.dat` files often contain **multiple measurements**. Typically:

| Measurement | Content | Purpose |
|---|---|---|
| 1 | `AdjCoilSens` | Coil sensitivity calibration (not used in this examples) |
| 2 (or last) | Your actual scan | The imaging data you want |

To find out what is inside, extract all measurements with the `--headerOnly` flag:

```bash
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# List protocol names for each measurement
siemens_to_ismrmrd -f gre_sphere.dat -z 1 --headerOnly 2>&1 | grep protocolName
siemens_to_ismrmrd -f gre_sphere.dat -z 2 --headerOnly 2>&1 | grep protocolName
```

Example output:
```
Measurement 1: <protocolName>AdjCoilSens</protocolName>    ← calibration, skip this
Measurement 2: <protocolName>gre_cor</protocolName>         ← your scan
```

> **Rule of thumb:** The last measurement is usually the actual scan data. Use `-z -1` (the default in the script) to automatically select the last one.

### Step 3: Convert to ISMRMRD HDF5

```bash
siemens_to_ismrmrd -f gre_sphere.dat -z 2 -o gre_sphere.h5
```

Or use the provided script, which also validates the output:

```bash
./convert_dat_to_h5.sh gre_sphere.dat 2
```

The script prints a validation summary:
```
Validation summary:
  Protocol:       gre_cor
  Scanner:        Siemens MAGNETOM Prisma
  Channels:       2
  Encoded matrix: 256x128x1
  Acquisitions:   128 total (128 imaging, 0 noise)
  Samples/readout:256
  Slice groups:   1
```

Check that:
- **Imaging acquisitions > 0** (if all are noise, you picked the wrong measurement)
- **Slice groups > 0** (at least one `ACQ_LAST_IN_SLICE` flag is set)

### Step 4: Reconstruct with Open Recon

Start the server in one terminal:
```bash
cd server
./run_server.sh r2ci_bart
```

Send the data in another terminal:
```bash
cd client
python3 client.py ../further_materials/04_raw_data_conversion/gre_sphere.h5
```

The client summary should show `Received  1 images` (or more, for multi-slice data).

### Step 5: View the result

```bash
cd client
python3 display.py out.h5
```

## Understanding Multi-Measurement Files

A single `.dat` file from a Siemens scanner can contain multiple measurement blocks. This is common in clinical sequences where calibration scans (noise measurements, coil sensitivity maps) are acquired before the actual imaging scan.

```
┌──────────────────────────────────────────┐
│  gre_sphere.dat                          │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ Measurement 1: AdjCoilSens        │  │  ← Coil calibration
│  │   256 readouts, 512 samples       │  │     (flags: noise)
│  │   128x64x64 encoded matrix        │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ Measurement 2: gre_cor (GRE)       │  │  ← Actual GRE scan
│  │   128 readouts, 256 samples       │  │     (flags: imaging)
│  │   256x128x1 encoded matrix        │  │
│  └────────────────────────────────────┘  │
│                                          │
└──────────────────────────────────────────┘
```

Always extract the **correct measurement number** (`-z 2` in this example). The conversion script warns you if it detects a calibration-only dataset.

## Troubleshooting

### All acquisitions flagged as noise

**Symptom:** The server logs `Unsupported data type Acquisition` for every readout, and returns 0 images.

**Cause:** You extracted a calibration measurement (e.g. `AdjCoilSens`) instead of the actual scan.

**Fix:** Use a different measurement number:
```bash
./convert_dat_to_h5.sh gre_sphere.dat 2
```

### Shape mismatch during reconstruction

**Symptom:** Server error like:
```
ValueError: could not broadcast input array from shape (2,512) into shape (2,128)
```

**Cause:** The calibration scan has different readout dimensions than the header's encoded matrix size.

**Fix:** Same as above — extract the correct measurement.

### siemens_to_ismrmrd not found

**Cause:** The devcontainer needs to be rebuilt, or the library path is not set.

**Fix:**
```bash
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

If `siemens_to_ismrmrd` is still missing, rebuild the devcontainer.

### No images returned by the server

**Symptom:** Client shows `Received 0 images`.

Possible causes:
- Wrong measurement extracted (see above)
- The data is not Cartesian k-space (the `r2ci_bart` module only handles Cartesian trajectories)
- The `ACQ_LAST_IN_SLICE` flag is not set on any readout (the module waits for this trigger)

## Background: What the Conversion Does

The `siemens_to_ismrmrd` tool:

1. **Parses** the Siemens `.dat` file header (protocol buffers containing scan parameters).
2. **Applies an XSL stylesheet** to map Siemens-specific parameters to the ISMRMRD XML header (matrix size, FOV, trajectory type, coil information, etc.).
3. **Reads raw k-space readouts** and converts them to ISMRMRD Acquisition objects with proper index fields (`kspace_encode_step_1`, `slice`, `repetition`, etc.) and flags (`ACQ_LAST_IN_SLICE`, `ACQ_IS_NOISE_MEASUREMENT`, etc.).
4. **Writes** everything to an HDF5 file in the standard ISMRMRD layout (`/dataset/xml`, `/dataset/data`).

The resulting `.h5` file is directly compatible with the Open Recon client (`client.py`) and server modules.
