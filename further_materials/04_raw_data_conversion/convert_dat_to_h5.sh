#!/bin/bash
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

# convert_dat_to_h5.sh — Convert a Siemens .dat raw data file to ISMRMRD .h5
#
# Usage:
#     ./convert_dat_to_h5.sh <input.dat> [measurement_number]
#
# Arguments:
#     input.dat            Path to the Siemens .dat raw data file
#     measurement_number   Which measurement to extract (default: last)
#                          Use -1 for the last measurement, 1 for the first, etc.
#
# Output:
#     Creates an .h5 file in the same directory as the input file,
#     with the same base name.
#
# Examples:
#     ./convert_dat_to_h5.sh gre_sphere.dat
#     ./convert_dat_to_h5.sh gre_sphere.dat 2
#     ./convert_dat_to_h5.sh gre_sphere.dat -1

set -e

# ─── Check arguments ───────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <input.dat> [measurement_number]"
    echo ""
    echo "  input.dat            Siemens raw data file"
    echo "  measurement_number   Which measurement to extract (default: last, i.e. -1)"
    echo ""
    echo "Tip: Use -l to list all measurements first:"
    echo "  siemens_to_ismrmrd -f <input.dat> -Z --headerOnly 2>&1 | grep protocolName"
    exit 1
fi

INPUT_DAT="$1"
MEAS_NUM="${2:--1}"

if [[ ! -f "${INPUT_DAT}" ]]; then
    echo "Error: File not found: ${INPUT_DAT}"
    exit 1
fi

# ─── Check that siemens_to_ismrmrd is available ────────────────────────
if ! command -v siemens_to_ismrmrd &> /dev/null; then
    echo "Error: siemens_to_ismrmrd not found on PATH."
    echo ""
    echo "If running inside the devcontainer, you may need to set:"
    echo "  export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH"
    echo ""
    echo "If not installed, rebuild the devcontainer (the Dockerfile"
    echo "installs it automatically)."
    exit 1
fi

# ─── Derive output filename ───────────────────────────────────────────
BASENAME="$(basename "${INPUT_DAT}" .dat)"
OUTDIR="$(dirname "${INPUT_DAT}")"
OUTPUT_H5="${OUTDIR}/${BASENAME}.h5"

if [[ -f "${OUTPUT_H5}" ]]; then
    echo "Warning: Output file already exists: ${OUTPUT_H5}"
    echo "         It will be overwritten."
fi

# ─── Run the conversion ───────────────────────────────────────────────
echo "Converting: ${INPUT_DAT}"
echo "  Measurement number: ${MEAS_NUM}"
echo "  Output file:        ${OUTPUT_H5}"
echo ""

export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}

siemens_to_ismrmrd \
    -f "${INPUT_DAT}" \
    -z "${MEAS_NUM}" \
    -o "${OUTPUT_H5}" \
    2>&1

echo ""
echo "──────────────────────────────────────────────"
echo "Conversion complete: ${OUTPUT_H5}"
echo "File size: $(du -h "${OUTPUT_H5}" | cut -f1)"
echo ""

# ─── Quick validation ─────────────────────────────────────────────────
python3 - "${OUTPUT_H5}" <<'PYEOF'
import sys
import ismrmrd
import re

h5_path = sys.argv[1]
dset = ismrmrd.Dataset(h5_path, 'dataset', False)
n = dset.number_of_acquisitions()

xml = dset.read_xml_header()
if isinstance(xml, bytes):
    xml = xml.decode('utf-8')

protocol = re.search(r'<protocolName>(.*?)</protocolName>', xml)
vendor = re.search(r'<systemVendor>(.*?)</systemVendor>', xml)
model = re.search(r'<systemModel>(.*?)</systemModel>', xml)
channels = re.search(r'<receiverChannels>(\d+)</receiverChannels>', xml)
mx = re.search(r'<encodedSpace>.*?<x>(\d+)</x>.*?<y>(\d+)</y>.*?<z>(\d+)</z>', xml, re.DOTALL)

noise = sum(1 for i in range(n) if dset.read_acquisition(i).is_flag_set(ismrmrd.ACQ_IS_NOISE_MEASUREMENT))
imaging = n - noise
last_slice = sum(1 for i in range(n) if dset.read_acquisition(i).is_flag_set(ismrmrd.ACQ_LAST_IN_SLICE))

acq0 = dset.read_acquisition(0)
print("Validation summary:")
print(f"  Protocol:       {protocol.group(1) if protocol else 'N/A'}")
print(f"  Scanner:        {vendor.group(1) if vendor else '?'} {model.group(1) if model else '?'}")
print(f"  Channels:       {channels.group(1) if channels else '?'}")
print(f"  Encoded matrix: {mx.group(1)}x{mx.group(2)}x{mx.group(3)}" if mx else "  Encoded matrix: N/A")
print(f"  Acquisitions:   {n} total ({imaging} imaging, {noise} noise)")
print(f"  Samples/readout:{acq0.number_of_samples}")
print(f"  Slice groups:   {last_slice}")

if imaging == 0:
    print("")
    print("  ⚠ WARNING: No imaging readouts found!")
    print("    All acquisitions are flagged as noise measurements.")
    print("    This is likely a calibration scan (e.g. AdjCoilSens).")
    print("    Try a different measurement number, e.g.:")
    print(f"      {sys.argv[0]} <input.dat> 2")

dset.close()
PYEOF

echo ""
echo "To reconstruct this file, run:"
echo "  cd server && ./run_server.sh r2ci_bart"
echo "  cd client && python3 client.py ${OUTPUT_H5}"
