# Client

The client sends MRD-formatted data to a running server and saves the reconstructed output.

## Files

| File | Description |
|---|---|
| `client.py` | Main client script. Reads an `.h5` input file, streams acquisitions/images to the server over TCP, and saves the server's response to an output `.h5` file. |
| `run_client.sh` | Convenience wrapper that selects a test dataset and calls `client.py`. Edit it to switch input files. |
| `display.py` | Visualizes the reconstructed images stored in `out.h5`. |
| `debug_ui_data.json` | Simulates the scanner UI parameters that Open Recon passes to the server at runtime. |
| `out.h5` | Output file written by `client.py` after a successful reconstruction (not committed to git). |

## Quick Start

Start the server first (see [`server/Readme.md`](../server/Readme.md)), then in a second terminal:

```bash
cd client
./run_client.sh
```

This sends the selected test dataset to the server on `localhost:9002` and writes the result to `out.h5`.  
Visualise the result with:

```bash
python3 display.py out.h5
```

## Selecting Input Data

`run_client.sh` selects the dataset automatically based on `OR_MODULE` (passed as the first argument or read from the environment):

| `OR_MODULE` | Dataset |
|---|---|
| `r2ci_bart` | `tse_r2ci.h5` (default; `tse_r2ci_interleaved.h5` available as a commented-out alternative) |
| `i2i_invertcontrast` | `tse_i2i.h5` |

All datasets are located in [`test/data/`](../test/data/).

## Scanner UI Parameters (`debug_ui_data.json`)

At the scanner, Open Recon passes a JSON object with the UI field values to the server as an MRD text message. `debug_ui_data.json` replicates this locally so you can test parameter-driven behaviour without a scanner.

When you add a new UI parameter to `appl_spec.json`, add a matching entry here to be able to test it. Example:

```json
{
    "parameters": {
        "picsFlagsId": "-e -S"
    }
}
```

The server reads this object as `ui_data` and passes it to the active processing module.

To use a different UI data file for a single run, pass it with `-u`:

```bash
python3 client.py ../test/data/tse_i2i.h5 -u ../test/data/debug_ui_data_passthrough
```

The test runner supports a 6th optional field in each `tests.sh` entry to specify the UI data file per test (see [`test/Readme.md`](../test/Readme.md)).

## Output Format

`out.h5` is an ISMRMRD-compatible HDF5 file. Each run appends a new top-level group named by the current timestamp. Inside that group you will find:

```
<timestamp>/
    xml          – MRD XML header
    image_0/     – reconstructed image series
        data     – image array
        header   – per-image headers
        ...
```

> **Note:** `client.py` always appends a new timestamped group, even if the server returns no images (e.g. on a connection error). The test framework handles this correctly by searching for the last group that contains an `image_*` subgroup.

You can also inspect the file structure with `h5ls -r out.h5` or open it in Python with `h5py`.
 