# Dev Container

This folder defines the VS Code development container for the open_recon_bart project.
It gives every developer an identical, self-contained environment with all dependencies pre-installed — no manual setup on the host machine required.

## Files

| File | Description |
|---|---|
| `Dockerfile` | Builds the dev container image (base OS, base Python packages, Docker-in-Docker, CUDA). |
| `devcontainer.json` | VS Code configuration: build args, mounts, post-create/start commands, extensions, environment variables. |
| `install_extra.sh` | Post-create script that installs external tools (e.g. BART) and additional packages after the container is first created. |
| `certs/` | Optional folder for custom CA certificates (e.g. corporate proxies). Place `.pem` or `.crt` files here and they are imported automatically on container start. |

---

## What Is Installed

### Base image

`python:3.12-slim-bullseye` (Debian 11)

### Python packages (baked into the image via `Dockerfile`)

| Package | Version | Purpose |
|---|---|---|
| `ismrmrd` | 1.14.1 | MRD data format library used by server and client. |
| `h5py` | 3.12.1 | HDF5 file I/O for reading/writing `.h5` datasets. |
| `numpy` | 1.26.4 | Numerical arrays, used throughout server and test scripts. |
| `matplotlib` | 3.8.2 | Image display (`client/display.py`). |
| `pydicom` | 3.0.1 | DICOM support. |
| `check-jsonschema` | 0.33.3 | Validates `appl_spec.json` during Docker image build. |
| `pypulseq` | latest | Pulse sequence design (experimentally used in `pulseq/`). |

### Docker (Docker-in-Docker)

Docker **24.0.0** is installed inside the container to match the version required on the VA60 scanner baseline (`OPENRECON=BASELINE`).
The environment variable `DOCKER_API_VERSION=1.43` is set to ensure the Docker client inside the container communicates correctly with the Docker daemon, avoiding API version mismatch errors.

To switch to the latest Docker version instead, change the build argument in `Dockerfile`:

```dockerfile
ARG OPENRECON=LATEST   # installs latest Docker CE instead of 24.0.0
```

### GPU Support (optional)

GPU support is **disabled by default** (`OR_GPU_SUPPORT=0`). To enable CUDA 11.6 (required on the VA60 scanner's MaRS GPU):

1. In `.devcontainer/devcontainer.json`, set `OR_GPU_SUPPORT` to `"1"` in `build.args`:
   ```jsonc
   "build": {
       "dockerfile": "Dockerfile",
       "args": {
           "OR_GPU_SUPPORT": "1"
       }
   },
   ```
2. In the same file, uncomment `--gpus all` in `runArgs`:
   ```jsonc
   "runArgs": ["--privileged", "--gpus", "all"]
   ```
3. Rebuild the dev container.

Your host machine must have a CUDA ≥ 11.6 driver and the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed.

---

## `install_extra.sh` — Post-Create Installations

### Why this script exists

Some tools are too large, too version-sensitive, or require GPU-specific builds to be reliably baked into the `Dockerfile`. The `install_extra.sh` script runs **once**, automatically, after the container is first created (`postCreateCommand` in `devcontainer.json`). It is the right place for:

- Tools built from source (e.g. BART)
- Large ML frameworks that are optional or GPU-dependent (e.g. TensorFlow, PyTorch)
- Any dependency that depends on runtime context (e.g. CUDA availability)

> **Important:** The script runs with `set -e` — any failing command aborts the script and the error is reported in the VS Code terminal. Do **not** append `|| true` to suppress errors; silent failures will make tools appear missing with no diagnostic information.

### How environment variables are set

Because `postCreateCommand` runs in a **non-interactive, non-login shell**, `~/.bashrc` is not sourced during script execution. To ensure variables are available everywhere, the script uses a layered approach:

| Mechanism | Where it applies |
|---|---|
| `/etc/environment` | All PAM-authenticated sessions. Suitable for simple `KEY=value` exports. Does **not** support variable expansion, so `PATH` cannot be prepended here. |
| `/etc/profile.d/bart.sh` | All login and interactive shells. Supports `export PATH=...:$PATH` expansion. |
| `~/.bashrc` | Interactive terminals opened by the user (belt-and-suspenders fallback). |
| `remoteEnv` in `devcontainer.json` | VS Code injects these into **every** integrated terminal and task at the process level, before any shell starts. This is the most reliable mechanism and covers non-interactive contexts such as VS Code tasks and launch configurations. |

### CA certificates must be updated before any HTTPS operation

The `devcontainer.json` bind-mounts the host's SSL certificates into `/usr/local/share/ca-certificates` **before** `postCreateCommand` runs. However, `update-ca-certificates` (which processes those files into a trusted bundle) only runs later in `postStartCommand`. This means that on first container creation, Git has **no CA bundle** and any `git clone https://...` will fail with:

```
server certificate verification failed. CAfile: none CRLfile: none
```

`install_extra.sh` therefore runs `sudo update-ca-certificates` as its **very first step**, before any network operations.

### Currently installed by `install_extra.sh`

#### BART (Berkeley Advanced Reconstruction Toolbox)

BART is cloned and built from source into `/container/bart`:

- Version: `v0.9.00` (change the `git checkout` line to update)
- Built with: `make -j12` (CPU-only by default; set `OR_GPU_SUPPORT=1` for CUDA)
- Also installs `bart-view` via `apt`

The following environment variables are set (via all mechanisms described above):

```bash
BART_TOOLBOX_PATH=/container/bart
TOOLBOX_PATH=/container/bart
OMP_NUM_THREADS=1
PATH=/container/bart:$PATH
```

To manually re-run the installation (e.g. after changing the BART version tag):

```bash
bash .devcontainer/install_extra.sh
```

### Adding further tools to `install_extra.sh`

#### Example: additional Python packages (e.g. PyTorch, TensorFlow)

Add `pip install` calls at the end of the script. For GPU-conditional installs:

```bash
# Install PyTorch (CPU or CUDA depending on OR_GPU_SUPPORT)
if [ "${OR_GPU_SUPPORT:-0}" = "1" ]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu116
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi
```

```bash
# Install TensorFlow (GPU variant requires CUDA to be present in the image)
if [ "${OR_GPU_SUPPORT:-0}" = "1" ]; then
    pip install tensorflow[and-cuda]
else
    pip install tensorflow-cpu
fi
```

#### Example: another tool built from source

Follow the same pattern used for BART:

```bash
# Clone and build only if not already present
if [ ! -d "/container/mytool" ]; then
    git clone https://example.com/mytool.git /container/mytool
fi
cd /container/mytool && make -j$(nproc)

# Register environment variables system-wide
sudo bash -c 'echo "MYTOOL_PATH=/container/mytool" >> /etc/environment'
sudo bash -c 'echo "export PATH=/container/mytool:\$PATH" > /etc/profile.d/mytool.sh'
echo 'export PATH="/container/mytool:$PATH"' >> ~/.bashrc
```

Then add a matching entry to the `remoteEnv` block in `devcontainer.json`:

```jsonc
"remoteEnv": {
    "MYTOOL_PATH": "/container/mytool",
    "PATH": "/container/mytool:/container/bart:${containerEnv:PATH}"
}
```

> **Note:** `remoteEnv.PATH` must list **all** custom path entries in a single value, as it overrides the previous `PATH` entry rather than appending to it.

---

## VS Code Extensions

The following extensions are installed automatically in the container:

| Extension | Purpose |
|---|---|
| `ms-python.python` / `ms-python.vscode-pylance` | Python language support and type checking. |
| `ms-python.debugpy` | Python debugging. |
| `ms-toolsai.jupyter` | Jupyter notebook support. |
| `ms-azuretools.vscode-containers` | Docker container management. |
| `yzhang.markdown-all-in-one` | Markdown editing and preview. |
| `streetsidesoftware.code-spell-checker` | Spell checking. |
| `tomoki1207.pdf` | PDF preview. |

---

## Certificate Handling

On container start, the `postStartCommand` in `devcontainer.json` automatically imports:
- System CA certificates from the host (`/etc/ssl/certs`)
- Any `.pem` / `.crt` files placed in `.devcontainer/certs/`

This is useful in corporate environments where HTTPS traffic passes through a proxy with a custom root CA.

---

## Rebuilding the Container

After changing `Dockerfile` or `devcontainer.json`, rebuild via VS Code:

> **Command Palette** (`Ctrl+Shift+P`) → `Dev Containers: Rebuild Container`

After rebuilding, `install_extra.sh` runs automatically again as part of `postCreateCommand`.
