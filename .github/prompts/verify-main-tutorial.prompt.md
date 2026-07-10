---
description: "Execute the main tutorial steps end-to-end: run the server (r2ci_bart and i2i_invertcontrast), send data with the client, display results, validate schemas, and run the test suite."
agent: "agent"
tools: [execute, read, search]
---

Walk through every executable step in the main tutorial (Readme.md) and verify each one succeeds. Run the steps in order — each depends on the previous ones.

## Step 1: Run the r2ci_bart server and client

Start the server in one terminal and the client in another:

**Server (async — leave running):**
```bash
cd server && ./run_server.sh r2ci_bart
```

**Client:**
```bash
cd client && ./run_client.sh
```

Verify the client summary shows `Received 1 images` (not 0).

Then display the result:
```bash
cd client && python3 display.py out.h5
```

Verify it prints the image shape without errors.

Stop the server after this step.

## Step 2: Run the i2i_invertcontrast server and client

**Server (async):**
```bash
cd server && ./run_server.sh i2i_invertcontrast
```

**Client:**
```bash
cd client && ./run_client.sh i2i_invertcontrast
```

Verify the client summary shows received images > 0.

Display:
```bash
cd client && python3 display.py out.h5
```

Stop the server.

## Step 3: Schema validation

```bash
check-jsonschema --schemafile server/modules/r2ci_bart/doc/appl_spec_schema.json server/modules/r2ci_bart/doc/appl_spec.json
```

```bash
check-jsonschema --schemafile server/modules/i2i_invertcontrast/doc/appl_spec_schema.json server/modules/i2i_invertcontrast/doc/appl_spec.json
```

Both must output `ok -- validation done`.

## Step 4: Run the fast test suite

```bash
cd test && ./test_server.sh --speed fast
```

All tests must print `Test passed successfully!`.

## Step 5: Docker workflow

Build and run the Docker image:

**Server:**
```bash
cd server && ./run_docker.sh r2ci_bart
```

**Client:**
```bash
cd client && ./run_client.sh
python3 display.py out.h5
```

Verify received images > 0 and display works.

## Report

Summarize which steps passed and which failed. For failures, include the error output and suggest fixes.
