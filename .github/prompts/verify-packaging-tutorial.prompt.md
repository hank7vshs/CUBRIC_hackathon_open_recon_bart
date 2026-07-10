---
description: "Execute the packaging guide verification (further_materials/03_packaging_guide) — build Docker images in VA60 and VA70+ modes, verify labels, and inspect archive structure."
agent: "agent"
tools: [execute, read, search]
---

Verify the packaging concepts from `further_materials/03_packaging_guide/Readme.md` by building images and inspecting their labels and archive structure.

## Step 1: VA60 Docker build with embedded label

Build the Docker image in VA60 mode (default):

```bash
cd server && ./docker_build.sh
```

Verify the embedded label contains the correct appl_spec.json:

```bash
docker image inspect open_recon_server:latest \
    --format '{{ index .Config.Labels "com.siemens-healthineers.magneticresonance.openrecon.metadata:1.1.0" }}' \
    | base64 -d | python3 -m json.tool | head -5
```

The output must show the `general` section from `server/modules/${OR_MODULE}/doc/appl_spec.json`.

## Step 2: VA70+ (OCI) Docker build without label

Build the Docker image in OCI mode:

```bash
cd server && ./docker_build.sh --oci
```

Verify no label is embedded:

```bash
docker image inspect open_recon_server:latest --format '{{json .Config.Labels}}'
```

Expected output: `null` or `{}`. No `com.siemens-healthineers` key should appear.

## Step 3: Inspect image layers

Show the image history to verify the layer structure:

```bash
docker image history open_recon_server:latest
```

## Report

Summarize: VA60 label correctness, VA70+ label absence, and layer structure observations.
