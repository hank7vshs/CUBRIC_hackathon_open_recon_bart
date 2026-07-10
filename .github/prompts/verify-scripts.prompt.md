---
description: "Verify all shell scripts for syntax errors (bash -n) and validate all appl_spec.json files against their schemas."
agent: "agent"
tools: [execute, read, search]
---

Run the following verification steps in order. Stop and report if any step fails.

## Step 1: Shell script syntax check

Run `bash -n` on every shell script in the repository to catch syntax errors without executing them:

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

## Step 2: Schema validation

Validate every `appl_spec.json` against its schema. Run from the repository root:

```bash
cd server/modules/r2ci_bart/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json
```

```bash
cd server/modules/i2i_invertcontrast/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json
```

Expected output for each: `ok -- validation done`

If any new modules exist under `server/modules/`, validate those too.

## Report

Summarize the results: how many scripts checked, how many schemas validated, and whether all passed.
