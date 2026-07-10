#!/bin/bash
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
#
# Start the Python reconstruction server directly (without Docker).
#
# Usage:
#   ./run_server.sh # defaults to OR_MODULE
#   ./run_server.sh r2ci_bart
#   ./run_server.sh i2i_invertcontrast

set -e

OR_MODULE=${1:-$OR_MODULE}

# Point Python to the BART toolbox so that 'import bart' works inside the container
export BART_TOOLBOX_PATH=/container/bart

python3 server.py --or-module "${OR_MODULE}"
