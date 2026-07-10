#!/bin/bash
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
#
# Create an Open Recon Application Package.
#
# Usage:
#   ./create_archive.sh                  # VA60 (default)
#   ./create_archive.sh --va70           # VA70+ Alpaca package format
#   ./create_archive.sh --va70 --oci     # VA70+ with OCI-layout export
#
# VA60 output:  <Name>.zip  containing:
#   <Name>.tar         — Docker image (docker save)
#   <Name>.pdf         — application guide
#
# VA70+ output: <Name>.OpenReconPackage.zip  containing:
#   ApplSpec.json      — scanner UI parameters & metadata
#   Container.tar      — Docker image (docker save, or OCI layout with --oci)
#   Manual.pdf         — application guide (generated from markdown)
#   Properties.json    — Alpaca package metadata (auto-generated)

set -euo pipefail

HERE_DIR=$(pwd)

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
VA70_MODE=0
OCI_MODE=0
for arg in "$@"; do
    case "$arg" in
        --va70) VA70_MODE=1 ;;
        --oci)  OCI_MODE=1 ;;
    esac
done

# --oci implies --va70 (OCI layout is only relevant for VA70+)
if [[ "$OCI_MODE" -eq 1 ]]; then
    VA70_MODE=1
fi

# ---------------------------------------------------------------------------
# Docker version guard (VA60 only)
# The scanner's package installer (VA60) requires images built with Docker
# 24.0.x (the version installed in the devcontainer). Images built with a
# newer Docker engine may use a container-image format that the scanner
# cannot import. Abort early if the local Docker version does not match.
# ---------------------------------------------------------------------------
if [[ "$VA70_MODE" -eq 0 ]]; then
    REQUIRED_DOCKER_MAJOR=24
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || docker version --format '{{.Client.Version}}')
    DOCKER_MAJOR=${DOCKER_VERSION%%.*}

    if [[ "$DOCKER_MAJOR" -ne "$REQUIRED_DOCKER_MAJOR" ]]; then
        echo -e "\e[31mError:\tDocker version mismatch. Found ${DOCKER_VERSION}, but version ${REQUIRED_DOCKER_MAJOR}.x is required.\e[0m" >&2
        echo -e "\e[31m\tPlease run this script from inside the devcontainer, which ships Docker ${REQUIRED_DOCKER_MAJOR}.0.0.\e[0m" >&2
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Common setup
# ---------------------------------------------------------------------------
source server/opts.sh

if [ -z "${OR_MODULE}" ]; then
    echo -e "\e[31mError:\tCould not read OR_MODULE.\e[0m" >&2
    exit 1
fi
echo "Packaging for OR_MODULE: ${OR_MODULE}"

DOC_DIR="server/modules/${OR_MODULE}/doc"
if [ ! -d "${DOC_DIR}" ]; then
    echo -e "\e[31mError:\tDoc folder not found: ${DOC_DIR}\e[0m" >&2
    exit 1
fi

TDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "$TDIR"' EXIT

PKGDIR="${TDIR}/package"
mkdir -p "${PKGDIR}"

export CONFIG_FILE=appl_spec.json

# ---------------------------------------------------------------------------
# Extract metadata from appl_spec.json
# ---------------------------------------------------------------------------
read -r VENDOR ID VERSION <<< "$(python3 server/get_string_data.py "${DOC_DIR}/${CONFIG_FILE}")"
NAME_STR="OpenRecon_${VENDOR}_${ID}_V${VERSION}"

if [[ "$VA70_MODE" -eq 1 ]]; then
    OUTPUT_ZIP="${NAME_STR}.OpenReconPackage.zip"
else
    OUTPUT_ZIP="${NAME_STR}.zip"
fi

if [ -f "${OUTPUT_ZIP}" ]; then
    echo "ABORT: Archive ${OUTPUT_ZIP} exists already."
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Generate PDF from application_guide.md
# ---------------------------------------------------------------------------
_generate_pdf() {
    local pdf_dest="$1"

    if [ -f "${DOC_DIR}/application_guide.md" ]; then
        cp "${DOC_DIR}/application_guide.md" "${TDIR}/application_guide.md"

        # Append version control info when inside a git repo
        if [ -d ".git" ]; then
            echo -e "Repository Version:" >> "${TDIR}/application_guide.md"
            echo "$(git describe --always)" >> "${TDIR}/application_guide.md"

            UNCOMMITTED_CHANGE=$(git status --short)
            [ -n "$UNCOMMITTED_CHANGE" ] && echo -e "\n\nUncommitted Changes:\n\n${UNCOMMITTED_CHANGE}" >> "${TDIR}/application_guide.md"
        fi

        pandoc "${TDIR}/application_guide.md" -o "$pdf_dest" --pdf-engine=pdflatex \
            --number-sections \
            --highlight-style=tango \
            -V geometry:margin=1in \
            -V fontsize=11pt \
            -V documentclass=article

        rm "${TDIR}/application_guide.md"
        echo "PDF generated: $pdf_dest"
    else
        echo -e "\e[31mError:\tMarkdown file for application guide could not be found in ${DOC_DIR}/!\e[0m" >&2
        exit 1
    fi
}

# Check for an existing PDF first (VA60 convention)
PDF_FILE=$(find "${DOC_DIR}" -type f -iname "${NAME_STR}.pdf" | head -1)
if [ -n "$PDF_FILE" ]; then
    echo "Found existing PDF: $PDF_FILE"
    if [[ "$VA70_MODE" -eq 1 ]]; then
        cp "$PDF_FILE" "${PKGDIR}/Manual.pdf"
    else
        cp "$PDF_FILE" "${PKGDIR}/${NAME_STR}.pdf"
    fi
else
    if [[ "$VA70_MODE" -eq 1 ]]; then
        _generate_pdf "${PKGDIR}/Manual.pdf"
    else
        _generate_pdf "${PKGDIR}/${NAME_STR}.pdf"
    fi
fi

# ---------------------------------------------------------------------------
# 2. Build Docker image
# ---------------------------------------------------------------------------
if [[ "$VA70_MODE" -eq 1 ]]; then
    server/docker_build.sh --oci "${DOC_DIR}/${CONFIG_FILE}"
else
    server/docker_build.sh "${DOC_DIR}/${CONFIG_FILE}"
fi

# ---------------------------------------------------------------------------
# 3. Export Docker image as .tar
# ---------------------------------------------------------------------------
if [[ "$VA70_MODE" -eq 1 ]]; then
    TAR_DEST="${PKGDIR}/Container.tar"

    if [[ "$OCI_MODE" -eq 1 ]]; then
        echo "Exporting OCI-layout Container.tar..."
        if docker buildx version > /dev/null 2>&1 && \
           docker buildx build \
                --build-arg OR_MODULE="${OR_MODULE}" \
                --output "type=oci,dest=${TAR_DEST}" \
                server/ 2>&1; then
            echo "OCI export succeeded."
        else
            echo "OCI export not supported by current Docker driver — falling back to docker save (Docker V2 format)."
            docker save -o "${TAR_DEST}" "${IMAGE_NAME}:${IMAGE_TAG}"
        fi
    else
        echo "Exporting Docker V2 Container.tar..."
        docker save -o "${TAR_DEST}" "${IMAGE_NAME}:${IMAGE_TAG}"
    fi
else
    TAR_DEST="${PKGDIR}/${NAME_STR}.tar"
    docker save -o "${TAR_DEST}" "${IMAGE_NAME}:${IMAGE_TAG}"
fi

# ---------------------------------------------------------------------------
# 4. VA70+ extras: ApplSpec.json, Properties.json
# ---------------------------------------------------------------------------
if [[ "$VA70_MODE" -eq 1 ]]; then
    # Copy ApplSpec.json
    cp "${DOC_DIR}/${CONFIG_FILE}" "${PKGDIR}/ApplSpec.json"

    # --- Extract image digest from Container.tar ---
    _extract_digest() {
        local tar_file="$1"
        local tmpext
        tmpext=$(mktemp -d 2>/dev/null || mktemp -d -t 'tarext')

        # Check if this is OCI layout (has oci-layout file)
        tar xf "$tar_file" -C "$tmpext" 'oci-layout' 2>/dev/null || true

        if [ -f "$tmpext/oci-layout" ]; then
            # --- OCI layout ---
            tar xf "$tar_file" -C "$tmpext" 'index.json' 2>/dev/null || true

            local manifest_digest
            manifest_digest=$(python3 -c "
import json
with open('$tmpext/index.json') as f:
    idx = json.load(f)
digest = idx['manifests'][0]['digest'].replace('sha256:', '')
print(digest)
")
            tar xf "$tar_file" -C "$tmpext" "blobs/sha256/$manifest_digest" 2>/dev/null || true

            local config_digest
            config_digest=$(python3 -c "
import json
with open('$tmpext/blobs/sha256/$manifest_digest') as f:
    m = json.load(f)
print(m['config']['digest'].replace('sha256:', ''))
")
            echo "$config_digest"
        else
            # --- Docker V2: extract manifest.json ---
            tar xf "$tar_file" -C "$tmpext" 'manifest.json' 2>/dev/null || true

            local config_digest
            config_digest=$(python3 -c "
import json, os
with open('$tmpext/manifest.json') as f:
    m = json.load(f)
cfg = m[0]['Config']
digest = os.path.splitext(os.path.basename(cfg))[0]
print(digest)
")
            echo "$config_digest"
        fi

        rm -rf "$tmpext"
    }

    IMAGE_DIGEST=$(_extract_digest "${TAR_DEST}")
    echo "Extracted image digest: ${IMAGE_DIGEST}"

    # --- Generate Properties.json ---
    IMAGE_NAME_LOWER=$(echo "${ID}" | tr '[:upper:]' '[:lower:]')

    if command -v uuidgen > /dev/null 2>&1; then
        APP_GUID=$(uuidgen)
    else
        APP_GUID=$(python3 -c "
import uuid, hashlib
h = hashlib.sha256(b'${VENDOR}${ID}${VERSION}').hexdigest()
u = uuid.UUID(h[:32])
print(str(u))
")
    fi

    python3 -c "
import json
props = {
    'package_format': 'Alpaca',
    'application_guid': '${APP_GUID}',
    'image_name': 'local/${IMAGE_NAME_LOWER}:latest',
    'execution_location': 'local',
    'persistence': 'permanent',
    'image_digest': '${IMAGE_DIGEST}'
}
with open('${PKGDIR}/Properties.json', 'w') as f:
    json.dump(props, f, indent=2)
"
    echo "Properties.json generated."
fi

# ---------------------------------------------------------------------------
# 5. Create the output zip
# ---------------------------------------------------------------------------
cd "${PKGDIR}"
zip -r "${OUTPUT_ZIP}" .
cd "${HERE_DIR}"
cp "${PKGDIR}/${OUTPUT_ZIP}" .

echo ""
echo "============================================================"
echo "Package created: ${OUTPUT_ZIP}"
echo "Contents:"
unzip -l "${OUTPUT_ZIP}"
echo "============================================================"
