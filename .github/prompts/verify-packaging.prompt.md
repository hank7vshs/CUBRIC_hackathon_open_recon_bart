---
description: "Generate scanner-deployable archives in all supported formats (VA60, VA70+, VA70+ OCI) and verify their contents."
agent: "agent"
tools: [execute, read, search]
---

Generate and verify scanner-deployable archives in all three supported packaging formats. Each step builds on the previous one. **Delete any existing archive before each step** (the script aborts if a zip already exists).

## Step 1: VA60 archive

```bash
cd /workspaces/open_recon_bart
rm -f OpenRecon_*.zip OpenRecon_*.OpenReconPackage.zip
./create_archive.sh
```

Verify the archive:
```bash
unzip -l OpenRecon_*.zip
```

Expected: exactly 2 files — `<Name>.tar` and `<Name>.pdf`.

Verify the PDF starts with `%PDF-`:
```bash
ZIPFILE=$(ls OpenRecon_*.zip | head -1)
unzip -p "$ZIPFILE" "*.pdf" | head -c 5
echo
```

Clean up:
```bash
rm -f OpenRecon_*.zip
```

## Step 2: VA70+ Alpaca archive

```bash
cd /workspaces/open_recon_bart
./create_archive.sh --va70
```

Verify:
```bash
unzip -l OpenRecon_*.OpenReconPackage.zip
```

Expected: exactly 4 files — `ApplSpec.json`, `Container.tar`, `Manual.pdf`, `Properties.json`.

Verify Properties.json:
```bash
ZIPFILE=$(ls OpenRecon_*.OpenReconPackage.zip | head -1)
unzip -p "$ZIPFILE" Properties.json | python3 -m json.tool
```

Must contain `"package_format": "Alpaca"` and a valid `image_digest`.

Verify ApplSpec.json matches the module's appl_spec.json:
```bash
unzip -p "$ZIPFILE" ApplSpec.json | python3 -m json.tool | head -10
```

Clean up:
```bash
rm -f OpenRecon_*.OpenReconPackage.zip
```

## Step 3: VA70+ with OCI export

```bash
cd /workspaces/open_recon_bart
./create_archive.sh --va70 --oci
```

The OCI exporter may not be supported by the Docker driver in this devcontainer. The script must **fall back gracefully** to `docker save` and print a warning instead of aborting. Verify:
- Exit code is 0
- If fallback occurs, the message `OCI export not supported by current Docker driver` appears
- The resulting zip has the same 4-file structure as Step 2

```bash
unzip -l OpenRecon_*.OpenReconPackage.zip
```

Clean up:
```bash
rm -f OpenRecon_*.OpenReconPackage.zip
```

## Report

Summarize for each format: whether the archive was created successfully, its contents, and whether all validations passed.
