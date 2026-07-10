---
description: "Run the full AGENTS.md verification checklist — all 9 steps: script syntax, schema validation, host tests, Docker builds (VA60 + OCI), Docker tests, and all three packaging formats."
agent: "agent"
tools: [execute, read, search]
---

Execute the complete verification checklist from `AGENTS.md` in order. Each step depends on the previous ones succeeding. Stop and report if any step fails.

Read the "Verification Checklist" section from [AGENTS.md](../../AGENTS.md) for the full details. Here is the execution plan:

## Step 1: Shell script syntax

```bash
cd /workspaces/open_recon_bart && \
bash -n server/run_server.sh && \
bash -n server/run_docker.sh && \
bash -n server/docker_build.sh && \
bash -n server/opts.sh && \
bash -n create_archive.sh && \
bash -n test/test_server.sh && \
bash -n test/test_docker.sh && \
bash -n test/tests.sh && \
bash -n client/run_client.sh
```

All must return exit code 0.

## Step 2: Schema validation

```bash
cd /workspaces/open_recon_bart/server/modules/r2ci_bart/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json

cd /workspaces/open_recon_bart/server/modules/i2i_invertcontrast/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json
```

## Step 3: Host-mode test suite (fast)

```bash
cd /workspaces/open_recon_bart/test && ./test_server.sh --speed fast
```

All 5 tests must print `Test passed successfully!`.

## Step 4: Docker image build (VA60)

```bash
cd /workspaces/open_recon_bart/server && ./docker_build.sh
```

Verify the label:
```bash
docker image inspect open_recon_server:latest \
    --format '{{ index .Config.Labels "com.siemens-healthineers.magneticresonance.openrecon.metadata:1.1.0" }}' \
    | base64 -d | python3 -m json.tool | head -5
```

## Step 5: Docker image build (OCI / VA70+)

```bash
cd /workspaces/open_recon_bart/server && ./docker_build.sh --oci
```

Verify no label:
```bash
docker image inspect open_recon_server:latest --format '{{json .Config.Labels}}'
```

Expected: `null` or `{}`.

## Step 6: Docker-mode test suite (fast)

```bash
cd /workspaces/open_recon_bart/test && ./test_docker.sh --speed fast
```

All tests must pass.

## Step 7: Package creation — VA60

```bash
cd /workspaces/open_recon_bart
rm -f OpenRecon_*.zip OpenRecon_*.OpenReconPackage.zip
./create_archive.sh
unzip -l OpenRecon_*.zip
rm -f OpenRecon_*.zip
```

Must contain exactly 2 files: `.tar` and `.pdf`.

## Step 8: Package creation — VA70+

```bash
cd /workspaces/open_recon_bart
./create_archive.sh --va70
unzip -l OpenRecon_*.OpenReconPackage.zip
rm -f OpenRecon_*.OpenReconPackage.zip
```

Must contain exactly 4 files: `ApplSpec.json`, `Container.tar`, `Manual.pdf`, `Properties.json`.

## Step 9: Package creation — VA70+ with OCI

```bash
cd /workspaces/open_recon_bart
./create_archive.sh --va70 --oci
unzip -l OpenRecon_*.OpenReconPackage.zip
rm -f OpenRecon_*.OpenReconPackage.zip
```

Must fall back gracefully if OCI export is not supported. Same 4-file structure.

## Step 10: Raw data conversion tutorial (04)

Convert the example `.dat` file and verify the output:

```bash
cd /workspaces/open_recon_examples/further_materials/04_raw_data_conversion
./convert_dat_to_h5.sh gre_sphere.dat 2
```

Verify the `.h5` file was created and contains acquisitions:

```bash
python3 -c "
import ismrmrd
dset = ismrmrd.Dataset('gre_sphere.h5', 'dataset', False)
n = dset.number_of_acquisitions()
print(f'Acquisitions: {n}')
assert n > 0
dset.close()
print('OK')
"
```

Clean up:
```bash
rm -f gre_sphere.h5
```

## Step 11: Bash BART server tutorial (05)

Validate scripts:
```bash
bash -n /workspaces/open_recon_examples/further_materials/05_bash_ncat_server/server.sh && \
bash -n /workspaces/open_recon_examples/further_materials/05_bash_ncat_server/reconstruct.sh && \
python3 -m py_compile /workspaces/open_recon_examples/further_materials/05_bash_ncat_server/mrd_adapter.py
```

Start the socat server and run the client:

**Server (async):**
```bash
cd /workspaces/open_recon_examples/further_materials/05_bash_ncat_server && ./server.sh
```

**Client:**
```bash
cd /workspaces/open_recon_examples/client && python3 client.py -a localhost -p 9002 ../test/data/gre_r2ci.h5
```

Verify `Received     1 images` in the client summary. Stop the server.

## Report

Provide a summary table:

| Step | Description | Result |
|------|-------------|--------|
| 1 | Script syntax | ? |
| 2 | Schema validation | ? |
| 3 | Host tests (fast) | ? |
| 4 | Docker build VA60 | ? |
| 5 | Docker build OCI | ? |
| 6 | Docker tests (fast) | ? |
| 7 | VA60 package | ? |
| 8 | VA70+ package | ? |
| 9 | VA70+ OCI package | ? |
| 10 | Raw data conversion (04) | ? |
| 11 | Bash BART server (05) | ? |
