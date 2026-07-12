# Comparing `.devcontainer/Dockerfile` and `server/Dockerfile`

This repository has **two separate Dockerfiles** with two separate jobs. Understanding the difference is essential before adding anything new (like MRtrix3 or `Supervised_RNS_dMRI`'s dependencies) to either one — a step that belongs in one file usually does *not* belong in the other, and the reasons why are structural, not arbitrary.

| | `.devcontainer/Dockerfile` | `server/Dockerfile` |
|---|---|---|
| **Purpose** | Your interactive development environment — where you write, run, and debug modules | The exact image deployed to the scanner (VA60 MaRS) — what actually runs in production |
| **Who builds/runs it** | VS Code's Dev Containers extension (or `devcontainer` CLI), via `devcontainer.json` | Plain `docker build` (`docker_build.sh`) — no lifecycle hooks, no VS Code involved |
| **User** | Creates a non-root user `recoon` (UID 1000) with passwordless sudo; `USER $USERNAME` is set before files are copied in | No `USER` directive at all — everything, including the final `CMD`, runs as **root** |
| **BART** | *Not* built here — deferred to `install_extra.sh`, which runs via `postCreateCommand` after the container starts, landing in `/container/bart` (owned by `recoon`) | Built directly in the Dockerfile itself, as root, into `/bart` |
| **ISMRMRD** | Builds the **C++ library** from source (`ismrmrd` + `siemens_to_ismrmrd`) — needed for the raw `.dat` → `.h5` conversion tutorial | Only `pip install ismrmrd` (Python bindings) — the deployed server never converts raw `.dat` files itself |
| **Docker-in-Docker** | Installs full Docker CE (client + daemon) so it can build/run the `server/Dockerfile` image from inside itself | None — the deployed image never runs nested containers |
| **CUDA** | Same conditional CUDA 11.6 install, **plus** the NVIDIA Container Toolkit (needed for GPU passthrough into the nested Docker-in-Docker) | Same conditional CUDA 11.6 install, no Container Toolkit (nothing nested to pass GPU into) |
| **Pinned Python packages** | `h5py==3.12.1`, `ismrmrd==1.14.1`, `matplotlib==3.10.8`, `pydicom==3.0.1`, `numpy==2.4.2`, `check-jsonschema==0.33.3`, `pypulseq` | `numpy==2.4.2`, `matplotlib==3.10.8`, `ismrmrd` (**version currently unpinned** — worth aligning to `1.14.1` at some point) |
| **Extra apt tools** | `git-cola`, `wget`, `unzip`, `screen`, `pandoc`, `texlive-*` — documentation/PDF generation and interactive tooling, not needed at runtime | Only what BART's own build needs (`libfftw3-dev`, `libblas-dev`, `libpng-dev`, `liblapacke-dev`) plus basics |
| **Final layout** | `WORKDIR /container`, `COPY . /container` as `recoon`; ends in `CMD ["bash"]` — an interactive shell, nothing auto-starts | `WORKDIR /opt/code/python-ismrmrd-server`, `COPY . ...` as root; `CMD` directly launches `python3 server.py --or-module ${OR_MODULE}` |
| **Build args unique to this file** | `ARG OPENRECON=BASELINE` (which Docker CE version to install) | `ARG OR_MODULE` (which module the server launches at startup) |

## Why this matters when adding a new dependency (e.g. MRtrix3)

Ask two questions before writing a single line:

1. **Does this need to survive on the scanner, or is it just for my own development/testing?**
   Development-only tools (Copilot, `git-cola`, manual experimentation) belong only in `.devcontainer/Dockerfile` / `install_extra.sh` — or nowhere in a committed file at all, if it's purely a manual exercise. Anything the *reconstruction module itself calls at runtime* (MRtrix3 command-line tools, `Supervised_RNS_dMRI`'s Python dependencies) must be baked into `server/Dockerfile`, because that is the only file that ever gets built into the deployed image — there is no `postCreateCommand` equivalent for it. Once packaged and installed on the scanner, there is no manual step left to run.

2. **Given `server/Dockerfile` has no non-root user, what does that change?**
   Every `RUN` in `server/Dockerfile` already executes as root — no `sudo` prefix needed. Environment variables should be set with `ENV` (immediately visible to every process, including `docker exec`), not the `/etc/profile.d` + `~/.bashrc` layering that `install_extra.sh` needs to work around `postCreateCommand`'s "new shells only" limitation. New tools should land at a top-level path like `/mrtrix3`, following the existing `/bart` convention, rather than nested under a user-owned directory like `/container`.

## Where do I actually test my module? Do I need `server/Dockerfile` running for that?

**No — not for day-to-day development.** This is the single most important thing to internalize before writing any module code, because "client/server" in OpenRecon sounds like it requires two separate machines or containers. It doesn't. Both are just two local *processes* that happen to talk over a TCP socket (port `9002`) — and both can run side-by-side inside the same devcontainer you're already in. `server/Dockerfile` only enters the picture once you want to validate the actual deployment image, which is a separate, later, slower stage.

There are three distinct stages, and you should spend almost all of your time in the first one:

| Stage | Command | What it proves | When to use it |
|---|---|---|---|
| **1. Host-mode** | `cd server && ./run_server.sh supervised_rns_dmri` (Terminal 1) + `cd client && ./run_client.sh` (Terminal 2), or the VS Code **"Server + client"** debug launch profile (`F5`) | The module's logic itself — `process()`, the science, the MRD message handling | **Almost always.** This is the fastest loop: no Docker build, breakpoints work, both processes run natively against the devcontainer's own Python/BART/MRtrix3. |
| **2. Docker-mode** | `cd server && ./run_docker.sh supervised_rns_dmri` | That the *packaged image* (`server/Dockerfile`) behaves identically — i.e. that everything the module needs is actually baked in there too, not just present in the devcontainer | Occasionally, once you're happy with Stage 1 — this is where a missing `server/Dockerfile` dependency (MRtrix3, a Python package) first shows up as a real failure, and it's Docker-in-Docker under the hood so no extra machine is needed |
| **3. Packaging** | `./create_archive.sh` | Produces the actual scanner-installable `.zip` | Once, near the end — not something you re-run per code change |

A concrete failure mode this table is meant to prevent: writing and testing a module entirely in Stage 1, where everything works because the devcontainer has every tool manually installed — then discovering at Stage 2 (or worse, on the actual scanner) that `server/Dockerfile` never got the same dependency added, because that step was skipped. Stage 2 exists specifically to catch that gap before it reaches the scanner.
