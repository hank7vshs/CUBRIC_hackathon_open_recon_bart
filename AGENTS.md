# AGENTS.md

Guidance for AI coding agents working on this repository.

## Project Overview

This repository provides a Python-based Open Recon server for Siemens Healthineers MRI scanners (VA60). It runs inside a Docker container on the scanner's MaRS GPU and reconstructs k-space or image data using [BART](https://mrirecon.github.io/bart). It is structured as a tutorial with two working example modules.

**Repository layout:**

```
server/              # Packaged into the OpenRecon Docker image
  server.py          # TCP entry point; dispatches to the selected module
  run_server.sh      # Run directly on the host (no Docker)
  run_docker.sh      # Build + run the Docker image
  docker_build.sh    # Build image; embeds appl_spec.json label (VA60) or plain build (--oci for VA70+)
  opts.sh            # Shared config: Docker image name and tag
  get_string_data.py # Extract vendor/id/version from appl_spec.json (used by create_archive.sh)
  Dockerfile         # Open Recon Docker image; OR_MODULE injected via --build-arg
  src/               # Shared library (connection.py, mrdhelper.py, constants.py)
  modules/
    r2ci_bart/       # Raw k-space → complex image via BART (default, main template)
    i2i_invertcontrast/   # Pre-reconstructed images → contrast-inverted images
    supervised_rns_dmri/  # Pre-reconstructed DWI images → diffusion model fit (scaffold, pipeline not yet implemented)
client/              # Test client (not deployed to scanner)
  client.py          # Streams .h5 data to server, writes out.h5
  run_client.sh      # Wrapper: choose input dataset here
  display.py         # Visualise out.h5
  debug_ui_data.json # Simulates scanner UI parameters locally
test/
  test_server.sh     # Run test suite against host server (no Docker)
  test_docker.sh     # Run test suite against Docker container
  tests.sh           # Test definitions (edit to add tests)
  scripts/           # nrmse_test.py, check_zero.py
  data/              # Input .h5 files for tests
  ref/               # Reference reconstructions for NRMSE comparison
further_materials/   # Standalone background tutorials (Docker, appl_spec.json, packaging)
  01_docker_tutorial/          # Hands-on Docker introduction
  02_VA60_application_specification_tutorial/  # appl_spec.json authoring guide
  03_packaging_guide/          # VA60 vs VA70+ packaging formats and installation
  04_raw_data_conversion/      # Siemens .dat → ISMRMRD .h5 conversion
  05_bash_ncat_server/         # Minimal bash+socat+BART server (MRD-compatible, no Python server)
create_archive.sh    # Package server + docs into a scanner-deployable .zip (VA60 default; --va70 for Alpaca format)
```

Each module under `server/modules/<name>/` follows this structure:

```
<name>.py            # Module logic; exports process(connection, ui_data, mrd_header)
__init__.py          # Re-exports process()
doc/
  appl_spec.json     # Scanner UI parameters, metadata, OR workflow type
  appl_spec_schema.json
  application_guide.md  # IFU / device description
Readme.md            # Developer guide for this module
```

## Environment

The repository runs inside a VS Code **devcontainer** (Docker-in-Docker, BART compiled from source, CUDA 11.6). All commands below assume the devcontainer shell.

Key environment variables:
- `BART_TOOLBOX_PATH=/container/bart` — set by `run_server.sh`; required for `import bart`
- `OR_MODULE` — selects the active module in Docker (`run_docker.sh`, `Dockerfile`)
- `OR_GPU_SUPPORT=1` — enables CUDA in both Dockerfiles and `--gpus all` in `run_docker.sh`; set via `build.args` in `devcontainer.json`

## Build and Run Commands

### Run the server directly (fastest iteration)
```bash
cd server
./run_server.sh r2ci_bart          # or i2i_invertcontrast
```

### Run the client (second terminal)
```bash
cd client
./run_client.sh
python3 display.py out.h5
```

### Build and run inside Docker
```bash
cd server
./run_docker.sh r2ci_bart
```

### Build the Docker image only
```bash
cd server
./docker_build.sh
```

### Package for scanner deployment
Set `OR_MODULE=<name>` in `.devcontainer/devcontainer.json` → `containerEnv`, then:
```bash
./create_archive.sh              # VA60 (default)
./create_archive.sh --va70       # VA70+ Alpaca package format
./create_archive.sh --va70 --oci # VA70+ with OCI-layout export
```

## Testing

Always run the fast test suite after any code change:

```bash
cd test
./test_server.sh --speed fast
```

Full suite (includes slow multi-slice test):
```bash
./test_server.sh
```

Filter by module:
```bash
./test_server.sh --mode r2ci_bart
./test_server.sh --mode i2i_invertcontrast
```

Same interface works for Docker tests:
```bash
./test_docker.sh --speed fast
```

**Expected passing output:**
```
6.03e-07    1e-6    Test passed successfully!
```

**Test format** (defined in `test/tests.sh`):
```
"<eps> <module> <input.h5> <ref.h5> <fast|slow> [<ui-data>]"
```
- `eps`: maximum allowed NRMSE; the test passes when `eps > nrmse` (strict), so use `1e-10` rather than `0` when an exact match is expected.
- `input` and `ref`: bare filenames are looked up in `test/data/` and `test/ref/` respectively. A subfolder prefix (e.g. `ref/file.h5`) is resolved relative to `test/`, allowing files in `ref/` to be used directly as input without copying.
- `ui-data` *(optional)*: name of a JSON file in `test/data/` (without the `.json` extension) containing UI parameters to send. Defaults to `client/debug_ui_data.json` when omitted. Use this to supply test-specific UI parameters (e.g. `debug_ui_data_passthrough` to enable `sendOriginalBoolId=true`).

To add a test, append an entry to `test/tests.sh`. See the module `Readme.md` for per-module guidance.

**Updating reference files:** run the server/client manually, then copy `client/out.h5` to the relevant `test/ref/` file.

## Module Interface

Every module must export a single function:

```python
def process(connection, ui_data, mrd_header):
    ...
```

| Argument | Type | Description |
|---|---|---|
| `connection` | `src.connection.Connection` | Iterable MRD message stream; call `connection.send_image(img_list)` and `connection.send_close()` to return results |
| `ui_data` | `dict` | JSON-decoded scanner UI parameters (or `client/debug_ui_data.json` locally) |
| `mrd_header` | `ismrmrd.xsd` object | Parsed MRD XML header with matrix size, FOV, encoding info |

Read UI parameters with:
```python
value = mrdhelper.get_json_param(ui_data, 'yourParamId')
```

The server dispatches to the module via `importlib.import_module(f"modules.{or_module}")` — no changes to `server.py` are needed unless adding a new module to the `choices=` list in `argparse`.

## Adding a New Module

1. Create `server/modules/<name>/` with `__init__.py` (re-exporting `process`) and `<name>.py`.
2. Add `doc/appl_spec.json` and `doc/application_guide.md`.
3. Add `<name>` to the `choices=` list in `server.py`'s `argparse` block.
4. Add test entries to `test/tests.sh`.
5. Use `r2ci_bart` as the template for raw-to-complex-image workflows, or `i2i_invertcontrast` for image-to-image workflows.

## Code Style Conventions

- **Python**: follow existing module style — module-level docstring describing the `process()` signature, helper functions prefixed with `_`, `logging.info/debug/error` for all diagnostics (no `print()`).
- **Shell scripts**: `set -e` at the top; use `${VARIABLE}` quoting; path logic via `dirname "${BASH_SOURCE[0]}"`.
- **No formatter is enforced** — keep consistent indentation (4-space Python, 4-space bash).
- **Debug output**: write intermediate arrays/images to `DEBUG_FOLDER = "/tmp/share/debug/"` (only when that folder exists).
- **Logging level**: `logging.WARNING` in `basicConfig`, overridden to `DEBUG` via `logging.root.setLevel` — all `logging.debug()` calls are active at runtime.

## Documentation Conventions

**Always update the relevant `Readme.md` files, AGENTS.md and functions documentation when changing any interface, parameter, file path, or module structure.**

### Audience and tone
- Write for MRI researchers and engineers who are familiar with MRI acquisition but may be new to Docker and Python reconstruction pipelines.
- Use clear, natural language — avoid jargon where a plain description works just as well.
- Prefer short sentences and concrete examples over abstract descriptions.

### Where details live
- **Root `Readme.md`**: tutorial flow only — overview, setup, run, extend. No internal implementation details.
- **`server/modules/<name>/Readme.md`**: module-specific developer guide — pipeline diagram, UI parameters, how to customize the reconstruction, how to add a test.
- **`server/Readme.md`**: server architecture, `src/` library, how to add a module.
- **`test/Readme.md`**: how to run tests, test format, how to add a test case.
- **`client/Readme.md`**: how to use the test client and `display.py`.
- Deep implementation details (NRMSE formula, etc.) belong in the subfolder Readmes, not the root.

### What to keep updated
- If you add or rename a UI parameter in `appl_spec.json`, update the parameter table in the module's `Readme.md` and mirror it in `client/debug_ui_data.json`.
- If you add a new module, add its entry to `server/Readme.md` and the root `Readme.md` module table.
- If you change a test file name or reference path, update `test/Readme.md` and `test/tests.sh`.
- If `process()` arguments or the dispatch mechanism in `server.py` change, update the Module Interface section in this file and `server/Readme.md`.
- If `test_server.sh` was modified, check if `test_docker.sh` requires the same modifications.

## Key Files to Know

| File | What to edit |
|---| ---|
| `server/modules/r2ci_bart/r2ci_bart.py` | BART reconstruction block (`ecalib` + `pics`) |
| `server/modules/<name>/doc/appl_spec.json` | Add/remove scanner UI parameters |
| `client/debug_ui_data.json` | Mirror any new UI parameters here for local testing |
| `test/tests.sh` | Add regression tests |
| `.devcontainer/devcontainer.json` | Set `OR_MODULE` in `containerEnv` before packaging |
| `server/opts.sh` | Docker image name and tag shared by all Docker scripts |

## Common Pitfalls

- **`i2i_invertcontrast` expects pre-reconstructed images**: the module only accepts `MRD_MESSAGE_ISMRMRD_IMAGE` messages. Sending raw k-space acquisitions will be ignored and no images will be returned.
- **`import bart` fails**: `BART_TOOLBOX_PATH` is not set. `run_server.sh` sets it automatically; outside that script, `export BART_TOOLBOX_PATH=/container/bart` first.
- **`out.h5` has no image group**: the server returned no images (check server terminal for errors). `display.py` and `nrmse_test.py` both raise `KeyError: "No image_* group found"` in this case.
- **k-space buffer size mismatch**: use `group[0].data.shape[1]` (actual acquired readout samples) rather than `mrd_header.encoding[0].encodedSpace.matrixSize.x` (header value) — they differ by 2× when readout oversampling is active.
- **Docker port conflict**: `run_docker.sh` stops any existing container with the same name before starting a new one — this is intentional.
- **`create_archive.sh` aborts if zip already exists**: delete or rename the existing `.zip` first.

## Verification Checklist

After any significant change, run through this checklist in order to verify the repository is fully functional. Each step depends on the previous ones succeeding. Stop and investigate if any step fails.

### 1. Shell script syntax

Check all scripts for syntax errors without executing them:

```bash
bash -n server/run_server.sh && \
bash -n server/run_docker.sh && \
bash -n server/docker_build.sh && \
bash -n server/opts.sh && \
bash -n create_archive.sh && \
bash -n test/test_server.sh && \
bash -n test/test_docker.sh && \
bash -n test/tests.sh && \
bash -n client/run_client.sh && \
bash -n further_materials/04_raw_data_conversion/convert_dat_to_h5.sh && \
bash -n further_materials/05_bash_ncat_server/server.sh && \
bash -n further_materials/05_bash_ncat_server/reconstruct.sh && \
python3 -m py_compile further_materials/05_bash_ncat_server/mrd_adapter.py
```

All must return exit code 0 with no output.

### 2. Schema validation

Verify every `appl_spec.json` is valid against its schema:

```bash
cd server/modules/r2ci_bart/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json

cd server/modules/i2i_invertcontrast/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json
```

Expected output for each: `ok -- validation done`

### 3. Host-mode test suite (fast)

This is the primary regression test. It starts the server, sends test data via the client, and compares the output against reference reconstructions using NRMSE:

```bash
cd test
./test_server.sh --speed fast
```

There are currently 5 tests (3 × `r2ci_bart`, 2 × `i2i_invertcontrast`). Every test must print `Test passed successfully!`. Any `FAILED` line means the reconstruction output does not match the reference within the allowed error margin.

### 4. Docker image build (VA60 mode)

Build the Docker image with the VA60 label:

```bash
cd server
./docker_build.sh
```

Verify the embedded label decodes to the correct `appl_spec.json`:

```bash
docker image inspect open_recon_server:latest \
    --format '{{ index .Config.Labels "com.siemens-healthineers.magneticresonance.openrecon.metadata:1.1.0" }}' \
    | base64 -d | python3 -m json.tool | head -5
```

The output must show the `general` section from `server/modules/${OR_MODULE}/doc/appl_spec.json`, not stale or example data.

### 5. Docker image build (OCI / VA70+ mode)

```bash
cd server
./docker_build.sh --oci
```

Verify no label is embedded:

```bash
docker image inspect open_recon_server:latest --format '{{json .Config.Labels}}'
```

Expected output: `null` (or `{}`). If any `com.siemens-healthineers` key appears, the Dockerfile may contain a hardcoded `LABEL` that should be removed.

### 6. Docker-mode test suite (fast)

Runs the same tests as step 3 but inside the Docker container:

```bash
cd test
./test_docker.sh --speed fast
```

All tests must pass. This additionally validates that the Dockerfile, `CMD`, and the server's in-container startup work end-to-end.

### 7. Package creation — VA60

```bash
cd /workspaces/open_recon_bart
./create_archive.sh
```

Verify the resulting zip:
- Filename: `OpenRecon_<Vendor>_<Id>_V<Version>.zip`
- Must contain exactly 2 files: `<Name>.tar` and `<Name>.pdf`
- The `.tar` must contain the Docker image with the correct label
- The `.pdf` must be a valid PDF (starts with `%PDF-`)

```bash
unzip -l OpenRecon_*.zip
```

Delete the zip before proceeding (the script aborts if it already exists).

### 8. Package creation — VA70+

```bash
./create_archive.sh --va70
```

Verify the resulting zip:
- Filename: `OpenRecon_<Vendor>_<Id>_V<Version>.OpenReconPackage.zip`
- Must contain exactly 4 files: `ApplSpec.json`, `Container.tar`, `Manual.pdf`, `Properties.json`
- `Properties.json` must have `"package_format": "Alpaca"` and a valid `image_digest`
- `ApplSpec.json` must match the module's `appl_spec.json`
- The Docker image in `Container.tar` must **not** have the appl_spec label

```bash
unzip -l OpenRecon_*.OpenReconPackage.zip
```

Delete the zip before proceeding.

### 9. Package creation — VA70+ with OCI

```bash
./create_archive.sh --va70 --oci
```

The OCI exporter may not be supported by the Docker driver in the devcontainer (Docker 24.0.0 with the default driver). The script must **fall back gracefully** to `docker save` and print a warning instead of aborting. Verify:
- The archive is created successfully (exit code 0)
- The fallback message appears: `OCI export not supported by current Docker driver`
- The resulting zip has the same 4-file structure as step 8

### Quick smoke test (minimum after small changes)

If time is limited, steps 1 + 3 are the minimum:

```bash
bash -n server/run_server.sh && bash -n server/docker_build.sh && \
bash -n create_archive.sh && bash -n test/test_server.sh && \
bash -n test/test_docker.sh && bash -n test/tests.sh && \
bash -n further_materials/04_raw_data_conversion/convert_dat_to_h5.sh && \
bash -n further_materials/05_bash_ncat_server/server.sh && \
bash -n further_materials/05_bash_ncat_server/reconstruct.sh && \
python3 -m py_compile further_materials/05_bash_ncat_server/mrd_adapter.py

cd test && ./test_server.sh --speed fast
```
