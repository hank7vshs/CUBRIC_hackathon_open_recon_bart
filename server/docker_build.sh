#!/bin/bash
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
#
# Build the Docker image for Open Recon.
#
# Usage:
#   ./docker_build.sh [--oci] [path/to/appl_spec.json]
#
# Modes:
#   (default / VA60)  Validates appl_spec.json, base64-encodes it, and embeds
#                     it as a Docker label — the format expected by VA60.
#   --oci  (VA70+)    Validates appl_spec.json but does NOT embed it as a
#                     Docker label. VA70+ reads ApplSpec.json from the package
#                     zip instead.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
OCI_MODE=0
JSON_ARG=""
for arg in "$@"; do
    case "$arg" in
        --oci) OCI_MODE=1 ;;
        *)     JSON_ARG="$arg" ;;
    esac
done

source "${SCRIPT_DIR}/opts.sh"

DEFAULT_JSON="$SCRIPT_DIR/modules/${OR_MODULE}/doc/appl_spec.json"
JSON_FILE="${JSON_ARG:-$DEFAULT_JSON}"

if [[ ! -f "$JSON_FILE" ]]; then
    echo "Error: JSON file '$JSON_FILE' not found."
    exit 1
fi

# Validate appl_spec.json against its schema
if ! python3 -m check_jsonschema "$JSON_FILE" --schemafile "$(dirname "$JSON_FILE")/appl_spec_schema.json"; then
    exit 1
fi

echo "Building image for module: ${OR_MODULE}"

if [[ "$OCI_MODE" -eq 1 ]]; then
    # --- VA70+ (OCI / Alpaca) -----------------------------------------------
    # No label embedding — VA70+ reads ApplSpec.json from the package zip.
    docker build \
        --build-arg OR_MODULE="${OR_MODULE}" \
        --build-arg OR_GPU_SUPPORT="${OR_GPU_SUPPORT:-0}" \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        "$SCRIPT_DIR"
else
    # --- VA60 (default) -----------------------------------------------------
    # Embed appl_spec.json as a base64-encoded Docker label.
    ENCODED_JSON=$(base64 -w 0 "$JSON_FILE")  # -w 0 avoids line breaks
    docker build \
        --label "com.siemens-healthineers.magneticresonance.openrecon.metadata:1.1.0=$ENCODED_JSON" \
        --build-arg OR_MODULE="${OR_MODULE}" \
        --build-arg OR_GPU_SUPPORT="${OR_GPU_SUPPORT:-0}" \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        "$SCRIPT_DIR"
fi

echo "Docker image ${IMAGE_NAME}:${IMAGE_TAG} built successfully."

# Check the resulting image label (VA60 only):
# docker image inspect open_recon_server:latest --format '{{ index .Config.Labels "com.siemens-healthineers.magneticresonance.openrecon.metadata:1.1.0" }}'