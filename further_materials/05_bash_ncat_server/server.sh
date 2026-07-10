#!/bin/bash
# Minimal BART reconstruction server — bash + socat.
# Speaks the MRD binary wire protocol (compatible with client.py and Open Recon).
# -t 600: after client finishes sending, wait up to 10 min for BART to complete.
set -e
echo "Listening on port 9002..."
socat -t 600 TCP-LISTEN:9002,reuseaddr,fork EXEC:./reconstruct.sh
