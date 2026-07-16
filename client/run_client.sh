#!/bin/bash
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

set -eux

# clean up to avoid stacking data in h5 container
[ -f out.h5 ] && rm out.h5

DATA_PATH='../test/data'

OR_MODULE=${1:-$OR_MODULE}

if [[ "$OR_MODULE" == "r2ci_bart" ]]; then
    DATA="${DATA_PATH}"/'tse_r2ci.h5'
    #DATA="${DATA_PATH}"/'tse_r2ci_interleaved.h5'
elif [[ "$OR_MODULE" == "i2i_invertcontrast" ]]; then
    DATA="${DATA_PATH}"/'tse_i2i.h5'
elif [[ "$OR_MODULE" == "supervised_rns_dmri" ]]; then
    DATA="${DATA_PATH}"/'tse_i2i.h5'  # placeholder until real DWI test data exists
else
    echo "Error: Unsupported OR_MODULE '$OR_MODULE'."
    exit 1
fi

python3 client.py ${DATA}
