- [Open Recon Packaging Guide](#open-recon-packaging-guide)
  - [Overview](#overview)
  - [VA60 — Baseline Package](#va60--baseline-package)
    - [Package contents](#package-contents)
    - [How the label works](#how-the-label-works)
    - [Creating a VA60 package](#creating-a-va60-package)
    - [Docker version constraint](#docker-version-constraint)
  - [VA70+ — Alpaca Package](#va70--alpaca-package)
    - [Package contents](#package-contents-1)
    - [Properties.json](#propertiesjson)
    - [Image digest](#image-digest)
    - [Creating a VA70+ package](#creating-a-va70-package)
    - [OCI layout export](#oci-layout-export)
  - [Comparing the Two Formats](#comparing-the-two-formats)
  - [Automatic Conversion from VA60 to VA70+](#automatic-conversion-from-va60-to-va70)
  - [Installing Packages at the Scanner](#installing-packages-at-the-scanner)
    - [VA60](#va60)
    - [VA70+ (Numaris/Edge)](#va70-numarisedge)

# Open Recon Packaging Guide

This guide explains the two packaging formats supported by Open Recon and how `create_archive.sh` in this repository generates them.

## Overview

Open Recon applications are distributed as zip archives that contain a Docker image, an application specification, and documentation. The exact archive layout depends on the target scanner software version:

| Scanner version | Format name | Script flag | Archive extension |
|---|---|---|---|
| VA60, VA61 | Baseline | *(default)* | `.zip` |
| VA70A, VA80A, VB10A+ | Alpaca | `--va70` | `.OpenReconPackage.zip` |

Both formats carry the same Docker image and the same `appl_spec.json` content — they differ in *how* the metadata is packaged and *where* the scanner looks for it.

## VA60 — Baseline Package

### Package contents

A VA60 archive has a flat structure:

```
OpenRecon_<Vendor>_<Id>_V<Version>.zip
├── <Name>.tar          # Docker image (docker save)
└── <Name>.pdf          # Application guide
```

The `appl_spec.json` is **not** included as a separate file. Instead, it is embedded as a Docker image label during the build (see below).

### How the label works

`docker_build.sh` (VA60 mode) base64-encodes the `appl_spec.json` and attaches it to the image with:

```bash
docker build \
    --label "com.siemens-healthineers.magneticresonance.openrecon.metadata:1.1.0=<base64>" \
    ...
```

The scanner reads this label from the image metadata after importing the `.tar` — it never needs to start the container to discover the application specification.

### Creating a VA60 package

```bash
./create_archive.sh
```

This is the default mode. The script:
1. Validates `appl_spec.json` against its schema.
2. Builds the Docker image with the embedded label.
3. Exports the image via `docker save`.
4. Generates a PDF from `application_guide.md`.
5. Packages everything into a `.zip`.

### Docker version constraint

VA60 scanners run Docker 24.0.x. Images built with a newer Docker engine may use a container-image format that the VA60 installer cannot import. The script enforces this by checking that the local Docker major version is `24` — if not, it aborts with an error and asks you to run from inside the devcontainer.

## VA70+ — Alpaca Package

### Package contents

VA70+ uses the **Alpaca** package format. The archive has a structured layout:

```
OpenRecon_<Vendor>_<Id>_V<Version>.OpenReconPackage.zip
├── ApplSpec.json       # Application specification (plain JSON, not base64)
├── Container.tar       # Docker image (docker save or OCI layout)
├── Manual.pdf          # Application guide
└── Properties.json     # Package metadata (GUID, image name, digest)
```

The `appl_spec.json` is shipped as a **separate file** (`ApplSpec.json`) inside the archive. The Docker image does **not** carry it as a label.

### Properties.json

This file is unique to the Alpaca format. It tells the scanner how to identify and load the container:

```json
{
  "package_format": "Alpaca",
  "application_guid": "<GUID>",
  "image_name": "local/<imagename>:latest",
  "execution_location": "local",
  "persistence": "permanent",
  "image_digest": "<DIGEST>"
}
```

| Field | Description |
|---|---|
| `application_guid` | A unique identifier in GUID format (`00000000-0000-4444-8888-000000000001`). |
| `image_name` | The name under which the image will be loaded locally. Must contain only lowercase letters and digits. |
| `image_digest` | The **config digest** (sha256) of the Docker image. The scanner verifies this at runtime — a mismatch will cause the reconstruction to fail. |

`create_archive.sh --va70` generates this file automatically.

### Image digest

The scanner checks the image digest at runtime to ensure the correct image is loaded. The digest must be the **config digest** — not the manifest digest. This is important because:

- For **Docker V2** images: the config digest is extracted from `manifest.json` inside the `.tar`.
- For **OCI** images: Docker converts the OCI manifest to Docker V2 on import, which changes the manifest digest. The config digest remains unchanged, so it is the only reliable identifier.

`create_archive.sh` extracts the correct digest automatically from the exported `Container.tar`, regardless of whether it is Docker V2 or OCI format.

### Creating a VA70+ package

```bash
./create_archive.sh --va70
```

The script:
1. Validates `appl_spec.json` against its schema.
2. Builds the Docker image **without** a label (VA70+ reads the spec from the zip).
3. Exports the image via `docker save`.
4. Generates a PDF from `application_guide.md`.
5. Copies `appl_spec.json` into the archive as `ApplSpec.json`.
6. Extracts the image config digest from `Container.tar`.
7. Generates `Properties.json`.
8. Packages everything into a `.OpenReconPackage.zip`.

### OCI layout export

By default, `Container.tar` is exported in Docker V2 format (via `docker save`). You can optionally export in OCI layout:

```bash
./create_archive.sh --va70 --oci
```

This uses `docker buildx` to produce an OCI-layout tar. Both formats are accepted by VA70+. OCI may be preferable for newer tooling, but Docker V2 is the safer default. If the OCI exporter is not supported (e.g. because the Docker driver does not support it, or `buildx` is not available), the script falls back to `docker save` automatically and prints a warning.

## Comparing the Two Formats

| Aspect | VA60 (Baseline) | VA70+ (Alpaca) |
|---|---|---|
| Archive extension | `.zip` | `.OpenReconPackage.zip` |
| `appl_spec.json` location | Embedded as Docker image label (base64) | Separate file `ApplSpec.json` in the zip |
| `Properties.json` | Not present | Required (GUID, image name, digest) |
| Image export format | Docker V2 only | Docker V2 or OCI layout |
| Docker version constraint | Must be 24.0.x | No strict constraint |
| Installation method | Copy zip to scanner inbox folder | CLI: `syngo.MR.Digi.Utils.Console.exe store --install` |

## Automatic Conversion from VA60 to VA70+

Starting with Numaris/Edge NE_2501, the scanner's command-line interface can automatically convert VA60 Baseline packages to the Alpaca format:

```
syngo.MR.Digi.Utils.Console.exe store --install OpenRecon_<Vendor>_<Product>_<Version>.zip
```

This accepts the old `.zip` format directly, converts it internally, and installs the result. However:

- Automatic conversion only works for **Docker-style** (non-OCI) container images.
- Digital signatures from the original package are not carried over — converted applications are **not qualified for clinical use**.
- The converted files are written to a folder next to the source `.zip` and can be inspected or repackaged if needed.

If you are building from source (as in this repository), it is better to generate the Alpaca package directly with `./create_archive.sh --va70` rather than relying on automatic conversion.

## Installing Packages at the Scanner

### VA60

1. Exit the scanner's kiosk interface (`Tab` + `Del` + `NUM` + `+`).
2. Copy the `.zip` to the OpenRecon installer inbox:
   ```
   C:\Program Files\Siemens\Numaris\OperationalManagement\FileTransfer\incoming
   ```
3. Installation starts automatically. The zip is removed from the folder once processing begins. Allow a few minutes before checking.

### VA70+ (Numaris/Edge)

1. Exit kiosk mode and open an elevated command prompt.
2. Navigate to the Numaris/Edge installation directory:
   ```
   cd %MREDGEHOME%
   ```
3. Install the package:
   ```
   syngo.MR.Digi.Utils.Console.exe store --install-package C:\path\to\package.OpenReconPackage.zip
   ```
4. Check installation status:
   ```
   syngo.MR.Digi.Utils.Console.exe store --list
   ```
   When the status changes from "Installing" to "Installed", the application is ready. It will appear in the Open Recon parameter tab in the Examination UI.
