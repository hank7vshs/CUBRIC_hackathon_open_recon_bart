# Testing Framework

## Overview

The testing framework provides two tools:

| Script | When to use |
|---|---|
| `test_server.sh` | **Development** — runs the Python server directly on the host, no Docker required. Fastest iteration cycle. |
| `test_docker.sh` | **Pre-packaging** — runs the server inside the Docker container, matching the real scanner environment. Use this before generating a new OpenRecon archive. |

Both scripts have an **identical command-line interface**. Every flag, filter, and custom-test syntax described below applies to both unless explicitly noted.

## Quick Start

```bash
cd test

# Fastest check — no Docker needed
./test_server.sh --speed fast

# Full suite before packaging
./test_server.sh

# Same suite but inside Docker (rebuilds image only if not present)
./test_docker.sh --speed fast
```

Expected output for a passing test:
```
6.03e-07    1e-6    Test passed successfully!
```

## Defining Tests

### Default test suite

When called without positional arguments, both scripts source [`tests.sh`](tests.sh) and run every entry in `TESTS`:

```bash
TESTS=(
    # <eps>  <mode>               <data>                          <ref>                                      <speed>
    "1e-6 r2ci_bart          gre_r2ci.h5                  gre_pics_default_reco.h5                fast"
    "1e-6 r2ci_bart          tse_r2ci.h5                  tse_pics_default_reco.h5                fast"
    "6e-6 r2ci_bart          tse_r2ci_interleaved.h5      tse_interleaved_pics_default_reco.h5    fast"
    "1e-6 i2i_invertcontrast tse_i2i.h5                   tse_i2i_invertcontrast_reco.h5          fast"
    "1e-10 i2i_invertcontrast ref/tse_i2i_invertcontrast_reco.h5   ref/tse_i2i_invertcontrast_reco.h5   fast debug_ui_data_passthrough"
)
```

The last entry is a **passthrough test**: with `sendOriginalBoolId=true` (set in `debug_ui_data_passthrough.json`), the server returns the input unchanged, so the input and reference are the same file and the expected error is effectively zero (`1e-10`).

Each entry is a space-separated 5- or 6-tuple:

| Field | Allowed values | Description |
|---|---|---|
| `eps` | e.g. `1e-6` | Maximum NRMSE for the test to pass. |
| `mode` | `r2ci_bart` \| `i2i_invertcontrast` | Processing module. Passed to the server as `--or-module`. |
| `data` | filename or `subfolder/filename` | Input MRD dataset. Bare filenames are looked up in `data/`; a prefix such as `ref/file.h5` is resolved relative to the `test/` directory. |
| `ref` | filename or `subfolder/filename` | Reference reconstruction. Bare filenames are looked up in `ref/`; a prefix such as `ref/file.h5` is resolved relative to the `test/` directory. |
| `speed` | `fast` \| `slow` | Classification used by `--speed` filter. Mark tests that take more than ~10 s as `slow`. |
| `ui_data` | filename without `.json` *(optional)* | UI parameter file looked up in `test/data/` (without the `.json` extension). Defaults to `client/debug_ui_data.json` when omitted. Use this to pass test-specific UI parameters (e.g. `debug_ui_data_passthrough` for the `sendOriginalBoolId=true` test). |

Add your own tests by appending entries to the `TESTS` array in `tests.sh`.
See each module's `Readme.md` for module-specific guidance on writing tests.

### Single custom test

Pass all five fields directly on the command line — no `tests.sh` is sourced:

```bash
./test_server.sh 1e-6 r2ci_bart my_data.h5 my_ref.h5 fast
```

`my_data.h5` must exist in `data/` and `my_ref.h5` must exist in `ref/`.

### Override the tests file

Point `TESTS_FILE` at any shell file that defines a `TESTS` array in the same 5-field format:

```bash
TESTS_FILE=/path/to/my_tests.sh ./test_server.sh
```

## Filtering Tests

`--speed` and `--mode` can be combined freely. Only tests that match **both** filters are executed:

```bash
./test_server.sh                                        # all tests
./test_server.sh --speed fast                           # only tests tagged fast
./test_server.sh --speed slow                           # only tests tagged slow
./test_server.sh --mode r2ci_bart                       # only r2ci_bart tests
./test_server.sh --mode i2i_invertcontrast              # only i2i tests
./test_server.sh --speed fast --mode r2ci_bart          # fast AND r2ci_bart
```

`--speed all` and `--mode all` are accepted but equivalent to omitting the flag.

## Help

Each script prints its full usage with `-h`:

```bash
./test_server.sh -h
./test_docker.sh -h
```

## Files

| File / Folder | Description |
|---|---|
| `tests.sh` | Default test suite — edit this file to add or remove tests. |
| `test_server.sh` | Run tests against the Python server directly (no Docker). |
| `test_docker.sh` | Run tests against the Dockerized server. |
| `scripts/nrmse_test.py` | NRMSE comparison utility called by both test scripts. |
| `scripts/check_zero.py` | Verifies that an output file contains only zero values. |
| `data/` | Input MRD datasets (`.h5`) consumed by the client. |
| `ref/` | Reference reconstructions (`.h5`) used for NRMSE comparison. |

### Input datasets (`data/`)

| File | Mode | Description |
|---|---|---|
| `gre_r2ci.h5` | `r2ci_bart` | GRE k-space data, single slice. |
| `tse_r2ci.h5` | `r2ci_bart` | TSE k-space data, single slice. |
| `tse_r2ci_interleaved.h5` | `r2ci_bart` | TSE k-space data, multi-slice interleaved acquisition. |
| `tse_i2i.h5` | `i2i_invertcontrast` | TSE magnitude images, used for contrast-inversion test. |
| `debug_ui_data_passthrough.json` | `i2i_invertcontrast` | UI parameter override for the passthrough test (`sendOriginalBoolId: true`). |

### Reference reconstructions (`ref/`)

Each file is the expected output for the corresponding input dataset, generated with the default reconstruction parameters:

| File | Corresponding input |
|---|---|
| `gre_pics_default_reco.h5` | `gre_r2ci.h5` |
| `tse_pics_default_reco.h5` | `tse_r2ci.h5` |
| `tse_interleaved_pics_default_reco.h5` | `tse_r2ci_interleaved.h5` |
| `tse_i2i_invertcontrast_reco.h5` | `tse_i2i.h5` |

> **Updating references:** If you intentionally change the reconstruction (e.g. modify BART flags), regenerate the affected reference files by running the server/client manually and copying `client/out.h5` to the appropriate `ref/` file.
