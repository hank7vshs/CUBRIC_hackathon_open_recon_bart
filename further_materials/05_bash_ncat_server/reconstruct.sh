#!/bin/bash
# Reconstruction handler — invoked by socat for each connection.
# Receives MRD binary messages on stdin → saves to h5 → converts to CFL →
# runs BART → converts back to h5 → sends MRD image messages on stdout.
set -e
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
DIR=$(dirname "$(readlink -f "$0")")

# Receive MRD binary messages → save acquisitions to h5
python3 "$DIR/mrd_adapter.py" receive "$W/input.h5"

# Run the conversion + BART pipeline with stdout suppressed
{
    # h5 → BART CFL
    python3 "$DIR/mrd_adapter.py" h5tocfl "$W/input.h5" "$W/kspace"

    # ── BART reconstruction (edit this section) ──
    bart ecalib -m1 "$W/kspace" "$W/sens"
    bart pics -l1 -r0.01 "$W/kspace" "$W/sens" "$W/tmp"
    bart flip 2 "$W/tmp" "$W/result"

    # BART CFL → h5
    python3 "$DIR/mrd_adapter.py" cfltoh5 "$W/result" "$W/output.h5"
} >/dev/null 2>&1

# Send MRD image messages back (image data + close)
python3 "$DIR/mrd_adapter.py" send "$W/output.h5"
