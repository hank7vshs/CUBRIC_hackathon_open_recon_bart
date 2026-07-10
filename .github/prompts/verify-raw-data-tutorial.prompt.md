---
description: "Execute the raw data conversion tutorial (further_materials/04_raw_data_conversion) — convert the example .dat file to ISMRMRD .h5, validate the output, and reconstruct with the server."
agent: "agent"
tools: [execute, read, search]
---

Walk through the raw data conversion tutorial at `further_materials/04_raw_data_conversion/Readme.md`. Verify each step produces the expected output.

## Step 1: Script syntax check

```bash
bash -n further_materials/04_raw_data_conversion/convert_dat_to_h5.sh
```

Must return exit code 0.

## Step 2: Convert the example .dat file

```bash
cd further_materials/04_raw_data_conversion
./convert_dat_to_h5.sh gre_sphere.dat 2
```

Must succeed (exit code 0) and produce `gre_sphere.h5` in the same directory.

## Step 3: Validate the .h5 output

Verify the file exists and contains acquisitions:

```bash
python3 -c "
import ismrmrd
dset = ismrmrd.Dataset('further_materials/04_raw_data_conversion/gre_sphere.h5', 'dataset', False)
n = dset.number_of_acquisitions()
print(f'Acquisitions: {n}')
assert n > 0, 'No acquisitions found'
dset.close()
print('OK')
"
```

## Step 4: Reconstruct with the server

Start the server and send the converted file:

**Server (async):**
```bash
cd server && ./run_server.sh r2ci_bart
```

**Client:**
```bash
cd client && python3 client.py ../further_materials/04_raw_data_conversion/gre_sphere.h5
```

Verify the client summary shows `Received` images > 0.

Display:
```bash
cd client && python3 display.py out.h5
```

Stop the server.

## Step 5: Clean up

```bash
rm -f further_materials/04_raw_data_conversion/gre_sphere.h5
```

## Report

Summarize which steps passed and which failed. For failures, include the error output.
