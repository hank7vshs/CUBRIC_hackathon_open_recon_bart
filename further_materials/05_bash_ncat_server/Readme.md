# 05 — Bash BART Server with socat

A minimal MRD-compatible reconstruction server using **socat + bash + BART**. Python is only used for data format conversion — the server itself is one line of socat, the reconstruction is a bash script.

> **A reconstruction server is just a program that reads k-space from a socket, runs BART, and writes the result back.**

## Why this exists

BART has a **command-line interface**. You call `bart pics kspace sens result` from a terminal and it writes the output to disk — no Python API required. That makes it possible to build a working reconstruction server with nothing more than a TCP listener (socat) and a short shell script that calls BART.

This tutorial demonstrates two things:

1. **The server pattern is language-agnostic.** The main Open Recon examples use a Python server, but the server is just a process that reads MRD messages from a socket, reconstructs, and writes MRD messages back. Any language or tool that can do that works — bash, C++, Julia, MATLAB, or a chain of Unix pipes.

2. **Any command-line tool can become a server this way.** Replace the BART calls in `reconstruct.sh` with your own tool — an FFT binary, a denoising executable, an AI inference CLI — and you have a working Open Recon server. The socat + adapter pattern turns stdin/stdout programs into network services without writing any networking code.

The server speaks the MRD binary wire protocol and is compatible with `client.py` and Open Recon.

## Pipeline

```
                               reconstruct.sh
                              ┌─────────────────────────────────────────┐
client.py  ─MRD─→   socat  → │ mrd_adapter.py receive   (MRD → h5)      │
                              │ mrd_adapter.py h5tocfl   (h5 → CFL)      │
                              │ bart ecalib                              │
                              │ bart pics                                │
                              │ bart flip                                │
                              │ mrd_adapter.py cfltoh5   (CFL → h5)      │
           ←MRD─            ← │ mrd_adapter.py send      (h5 → MRD)      │
                              └─────────────────────────────────────────┘
```

All format conversions live in a single `mrd_adapter.py` with four subcommands. The core pipeline converts h5 to BART's CFL format, runs BART, and converts back.

## Files

| File | Purpose |
|---|---|
| `server.sh` | socat listener on port 9002 (MRD protocol) |
| `reconstruct.sh` | Per-connection handler: MRD → h5 → CFL → BART → CFL → h5 → MRD |
| `mrd_adapter.py` | All format conversions: `receive`, `send`, `h5tocfl`, `cfltoh5` |
| `Dockerfile` | Debian + socat + BART + Python (h5py, ismrmrd) |

## Quick start

Requirements: socat, BART, Python 3 with ismrmrd + h5py + numpy. All available in the devcontainer.

**Terminal 1 — start the server:**
```bash
cd further_materials/05_bash_ncat_server
./server.sh
```

**Terminal 2 — use the Python client:**
```bash
cd client
python3 client.py -a localhost -p 9002 ../test/data/gre_r2ci.h5
python3 display.py out.h5
```

This uses the same `client.py` that talks to the full Python server — the socat server is a drop-in replacement for raw-to-image workflows.

Any ISMRMRD `.h5` file from `test/data/` works:
```bash
python3 client.py -a localhost -p 9002 ../test/data/tse_r2ci.h5
```

### With Docker

```bash
cd further_materials/05_bash_ncat_server
docker build -t bart-socat-server .
docker run --rm -p 9002:9002 bart-socat-server

# In another terminal:
cd client
python3 client.py -a localhost -p 9002 ../test/data/gre_r2ci.h5
python3 display.py out.h5
```

## Customising the reconstruction

Edit the BART section in `reconstruct.sh`. For example, replace `ecalib` + `pics` with a simple inverse FFT:

```bash
bart fft -iu 7 "$W/kspace" "$W/result"
```

Or add regularisation flags:

```bash
bart ecalib -m1 "$W/kspace" "$W/sens"
bart pics -l1 -r0.001 -e -S "$W/kspace" "$W/sens" "$W/tmp"
bart flip 2 "$W/tmp" "$W/result"
```

The conversion functions in `mrd_adapter.py` do not need editing — they handle any matrix size automatically.

## How it works

- **`server.sh`** runs `socat -t 600 TCP-LISTEN:9002,reuseaddr,fork EXEC:./reconstruct.sh`. TCP connections have two independent directions. When the client finishes sending, it half-closes its write side. socat sees this as EOF on the child's stdin and by default waits only 0.5 seconds before killing the child — long before BART finishes. The `-t 600` flag extends that grace period to 10 minutes. Once `reconstruct.sh` exits, socat sends the output back and closes the connection normally. If the container is stopped during reconstruction, all processes are killed immediately and the connection is reset — no resources leak.
- **`reconstruct.sh`** calls `mrd_adapter.py` four times: `receive` to parse MRD messages and save acquisitions to h5, `h5tocfl` to convert to BART format, then after BART runs, `cfltoh5` to convert back to h5, and finally `send` to emit MRD image messages.
- **`mrd_adapter.py`** has four subcommands: `receive` reads MRD message IDs and payloads from stdin, keeping only the XML header and raw k-space acquisitions — config, text (UI data), images, and waveforms are consumed but discarded. `send` reads the ISMRMRD h5 output, serializes each image as `MRD_MESSAGE_ISMRMRD_IMAGE` (1022), and sends `MRD_MESSAGE_CLOSE` (4). `h5tocfl` extracts k-space from the h5 into BART CFL format `(readout, phase_encodes, 1, channels)`. `cfltoh5` reads BART CFL, normalizes, and writes an ISMRMRD h5 image readable by `display.py`.

## Limitations

- **No metadata** — header information (FOV, orientation, patient info) and UI parameters are stripped. The reconstruction uses k-space dimensions only.
- **Single-slice** — `h5tocfl` buffers all readouts into one k-space array. Multi-slice datasets will be collapsed into one reconstruction.
- **Educational** — for scanner deployment, use the full Python server in `server/` which handles MRD framing, multi-slice, and scanner UI parameters.
