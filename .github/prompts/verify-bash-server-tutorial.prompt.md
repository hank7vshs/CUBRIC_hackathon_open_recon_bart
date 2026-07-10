---
description: "Execute the bash BART server tutorial (further_materials/05_bash_ncat_server) — validate scripts, start the socat server, send data with client.py, and verify the reconstruction."
agent: "agent"
tools: [execute, read, search]
---

Walk through the bash BART server tutorial at `further_materials/05_bash_ncat_server/Readme.md`. Verify each step produces the expected output.

## Step 1: Script and Python syntax check

```bash
bash -n further_materials/05_bash_ncat_server/server.sh && \
bash -n further_materials/05_bash_ncat_server/reconstruct.sh && \
python3 -m py_compile further_materials/05_bash_ncat_server/mrd_adapter.py
```

All must return exit code 0.

## Step 2: Start the socat server and run the client

**Server (async — leave running):**
```bash
cd further_materials/05_bash_ncat_server && ./server.sh
```

Wait for the "Listening on port 9002..." message.

**Client:**
```bash
cd client && python3 client.py -a localhost -p 9002 ../test/data/gre_r2ci.h5
```

Verify the client summary shows:
- `Sent   256 acquisitions`
- `Received     1 images`

## Step 3: Verify the output

```bash
cd client && python3 display.py out.h5
```

Must print the image shape without errors.

Also verify the image data programmatically:

```bash
python3 -c "
import h5py, numpy as np
f = h5py.File('client/out.h5', 'r')
grp = f[list(f.keys())[-1]]
d = grp['image_0']['data'][()]
m = np.sqrt(d['real']**2 + d['imag']**2) if d.dtype.names else np.abs(d)
print(f'Shape: {d.shape}  Max: {np.round(m.max(), 4)}')
assert d.shape[-1] == 256 and d.shape[-2] == 256, 'Unexpected image size'
assert m.max() > 0, 'Image is all zeros'
print('OK')
"
```

Stop the server.

## Step 4: Test with a second dataset

Restart the server and send a different dataset:

**Server (async):**
```bash
cd further_materials/05_bash_ncat_server && ./server.sh
```

**Client:**
```bash
cd client && python3 client.py -a localhost -p 9002 ../test/data/tse_r2ci.h5
```

Verify received images > 0. Stop the server.

## Report

Summarize which steps passed and which failed. For failures, include the error output and suggest likely causes (e.g. port already in use, BART not found).
