---
description: "Execute the application specification tutorial (further_materials/02_VA60_application_specification_tutorial) — validate the template, verify schema checking, and test all parameter types."
agent: "agent"
tools: [execute, read, search]
---

Walk through the application specification tutorial at `further_materials/02_VA60_application_specification_tutorial/Readme.md`. This tutorial teaches how to author and validate `appl_spec.json` files.

## Step 1: Validate the template

Check that the provided template is valid against the schema:

```bash
cd further_materials/02_VA60_application_specification_tutorial && \
    python3 -m check_jsonschema application_specification_template.json \
    --schemafile application_specification_schema.json
```

Expected: `ok -- validation done`

## Step 2: Verify schema catches errors

Create a temporary copy of the template with a deliberate error (remove a required field), and confirm the schema validator rejects it:

```bash
cd further_materials/02_VA60_application_specification_tutorial && \
    python3 -c "
import json
with open('application_specification_template.json') as f:
    data = json.load(f)
del data['general']['id']
with open('/tmp/bad_appl_spec.json', 'w') as f:
    json.dump(data, f, indent=2)
" && \
    python3 -m check_jsonschema /tmp/bad_appl_spec.json \
    --schemafile application_specification_schema.json || echo "Schema correctly rejected invalid file"
```

The validator must report a validation error (non-zero exit code).

## Step 3: Validate the real module appl_spec files

Confirm the actual module specifications are valid:

```bash
cd server/modules/r2ci_bart/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json

cd server/modules/i2i_invertcontrast/doc && \
    python3 -m check_jsonschema appl_spec.json --schemafile appl_spec_schema.json
```

Both must output `ok -- validation done`.

## Report

Summarize: template validity, error detection, and real module validation results.
