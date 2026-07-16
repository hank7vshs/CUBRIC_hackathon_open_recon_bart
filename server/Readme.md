# Server

This folder contains all files that are packaged into the OpenRecon Docker image and deployed to the scanner.

## Files

| File / Folder | Description |
|---| ---|
| `server.py` | Entry point. Accepts one connection, routes it to the selected processing module, then exits. |
| `run_server.sh` | Run the server directly on the host (no Docker). |
| `run_docker.sh` | Build (if needed) and run the server inside the Docker container. |
| `docker_build.sh` | Build the Docker image. Embeds `appl_spec.json` as a label by default (VA60); pass `--oci` for VA70+ (no label). |
| `opts.sh` | Shared configuration: Docker image name (`open_recon_server`) and tag (`latest`). Sourced by all Docker-related scripts. |
| `get_string_data.py` | Extract `vendor`, `id`, and `version` fields from `appl_spec.json`. Used by `create_archive.sh` to derive the output filename. |
| `Dockerfile` | Image definition: installs BART, Python dependencies, copies `src/` and `modules/`. |
| `src/` | Shared Python library used by all processing modules. |
| `modules/` | Processing modules — one subfolder per OR module. |

## Processing Modules

The server selects a module at startup via `--or-module`. Each module lives in `modules/<name>/` and exports a single `process()` function.

| Module | OR workflow | Description |
|---|---|---|
| `r2ci_bart` *(default)* | Raw-to-complex-image | Buffers k-space per slice and reconstructs using BART (`ecalib` + `pics`). See [`modules/r2ci_bart/Readme.md`](modules/r2ci_bart/Readme.md). |
| `i2i_invertcontrast` | Image-to-image | Receives magnitude images and inverts their contrast. See [`modules/i2i_invertcontrast/Readme.md`](modules/i2i_invertcontrast/Readme.md). |
| `supervised_rns_dmri` *(scaffold)* | Image-to-image | Fits a diffusion model using an ML model trained with Realistic Noise Synthesis. Pipeline not yet implemented. See [`modules/supervised_rns_dmri/Readme.md`](modules/supervised_rns_dmri/Readme.md). |

## Run the Server Directly (No Docker)

Requires BART on the host with `BART_TOOLBOX_PATH` set.

```bash
cd server
./run_server.sh                    # default: r2ci_bart
./run_server.sh r2ci_bart
./run_server.sh i2i_invertcontrast
```

The server listens on port `9002` and exits after serving one client connection.

## Run the Server in Docker

```bash
cd server
./run_docker.sh                    # default: r2ci_bart
./run_docker.sh r2ci_bart
./run_docker.sh i2i_invertcontrast
```

`run_docker.sh` will:
1. Build the image (`open_recon_server:latest`) if it does not already exist.
2. Stop and remove any existing container with the same name.
3. Start a new container, forwarding port `9002` and passing the selected module via the `OR_MODULE` environment variable.

## Build the Docker Image Manually

```bash
cd server
./docker_build.sh                  # VA60 (default): embeds appl_spec.json as label
./docker_build.sh --oci             # VA70+: no label, metadata in package zip
```

The active module for the packaged image is determined by the `OR_MODULE` environment variable. `docker_build.sh` reads `OR_MODULE` from the host environment (set in `.devcontainer/devcontainer.json` → `containerEnv`) and passes it as a `--build-arg` to the Dockerfile, which stores it as `ENV OR_MODULE`. At build time, the script uses this value to locate `modules/<name>/doc/appl_spec.json`, validates it against its schema, base64-encodes it, and embeds it as a Docker image label required by the VA60 OpenRecon platform. In `--oci` mode (VA70+), the schema validation still runs but no label is embedded — VA70+ reads `ApplSpec.json` from the package zip instead.

## Adding a New Module

1. Create `modules/<name>/` with `<name>.py` (exports `process()`) and `__init__.py` (re-exports `process()`).
2. Add a `doc/` subfolder with `appl_spec.json` and `application_guide.md`. Use an existing module's `doc/` as a starting point.
3. Add `<name>` to the `choices=` list in `server.py`'s `argparse` block.
4. Add test entries to `test/tests.sh`. See [`test/Readme.md`](../test/Readme.md) for the test format.
5. Use `r2ci_bart` as the template for raw-to-complex-image workflows, or `i2i_invertcontrast` for image-to-image workflows.

## Environment Variables

| Variable | Set by | Description |
|---|---|---|
| `BART_TOOLBOX_PATH` | `run_server.sh` | Path to the BART installation. Required for `import bart`. |
| `OR_MODULE` | `run_docker.sh`, `Dockerfile` | Selects the active processing module inside the Docker container. |
| `OR_GPU_SUPPORT` | `devcontainer.json` build args | Set to `1` to enable CUDA in both Dockerfiles and `--gpus all` in `run_docker.sh`. |

## Shared Library (`src/`)

| Module | Description |
|---|---|
| `connection.py` | Low-level MRD protocol: read/write MRD message frames over a TCP socket. |
| `mrdhelper.py` | Utility functions for MRD header and image metadata manipulation. |
| `constants.py` | MRD message type IDs and struct format strings. |

## MRD Message Flow

[MRD (Magnetic Resonance Data)](https://ismrmrd.readthedocs.io/) is an open standard for streaming MRI data. In this repository, the scanner (or test client) connects to the server over TCP and exchanges typed binary messages. Each message starts with a 2-byte ID identifying its type, followed by the payload.

The message exchange follows this sequence:

```
Client (scanner / test client)              Server
    │                                          │
    ├─── MRD_MESSAGE_CONFIG_TEXT ──────────────►│  UI parameters as JSON
    │                                          │
    ├─── MRD_MESSAGE_METADATA_XML_TEXT ────────►│  MRD XML header (matrix size, FOV, encoding)
    │                                          │
    ├─── MRD_MESSAGE_ISMRMRD_ACQUISITION ─────►│  k-space readouts (r2ci workflow)
    │    ... repeated per readout line ...      │  — or —
    ├─── MRD_MESSAGE_ISMRMRD_IMAGE ───────────►│  reconstructed images (i2i workflow)
    │    ... repeated per image ...             │
    │                                          │
    │◄── MRD_MESSAGE_ISMRMRD_IMAGE ────────────┤  reconstructed / processed images
    │    ... repeated per output image ...      │
    │                                          │
    ├─── MRD_MESSAGE_CLOSE ───────────────────►│  end of stream
    │◄── MRD_MESSAGE_CLOSE ────────────────────┤
    │                                          │
```

In a module's `process()` function, you iterate `connection` to receive incoming messages as typed Python objects (`ismrmrd.Acquisition` or `ismrmrd.Image`), and call `connection.send_image()` to return results. The binary framing is handled entirely by `connection.py` — modules never deal with raw TCP.
