#!/usr/bin/env python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
"""
check_zero.py -- Verify that every image data array in an HDF5 file is zero.

Usage:
    python3 check_zero.py <output.h5>

Exits with code 0 and prints a PASS message if all pixels are zero.
Exits with code 1 and prints a FAIL message otherwise.
"""

import sys
import h5py
import numpy as np


def main():
    if len(sys.argv) != 2:
        print("Usage: check_zero.py <output.h5>")
        sys.exit(1)

    out_path = sys.argv[1]

    with h5py.File(out_path, 'r') as f:
        arrays = []

        def _collect(name, obj):
            if isinstance(obj, h5py.Dataset) and 'data' in name:
                arrays.append((name, obj[()]))

        f.visititems(_collect)

    if not arrays:
        print("FAIL: no data arrays found in output file")
        sys.exit(1)

    for name, arr in arrays:
        maxval = float(np.max(np.abs(arr.astype(np.float64))))
        if maxval != 0.0:
            print(f"FAIL: dataset '{name}' is not zero (max absolute value = {maxval})")
            sys.exit(1)

    print("PASS: all pixels are zero  (image − itself = 0,  NRMSE = 0)")


if __name__ == '__main__':
    main()
