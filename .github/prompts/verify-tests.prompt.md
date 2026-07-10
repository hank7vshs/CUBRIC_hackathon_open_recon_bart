---
description: "Run the fast host-mode test suite (test_server.sh --speed fast) to verify all reconstructions match their references."
agent: "agent"
tools: [execute, read, search]
---

Run the fast regression test suite against the host server. This starts the server for each module, sends test data via the client, and compares the output against reference reconstructions using NRMSE.

## Execution

Run from the repository root:

```bash
cd test && ./test_server.sh --speed fast
```

## Expected result

There are currently 5 fast tests (3 x r2ci_bart, 2 x i2i_invertcontrast). Every test must print `Test passed successfully!`. Any `FAILED` line means the reconstruction output does not match the reference within the allowed error margin.

## On failure

If any test fails:
1. Report which test(s) failed and the NRMSE values
2. Check the server terminal output for errors (CUDA errors, import failures, shape mismatches)
3. Suggest likely causes based on the error messages
