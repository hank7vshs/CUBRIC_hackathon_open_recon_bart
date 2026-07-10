#!/bin/bash
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OR_MODULE=${1:-$OR_MODULE}

# IMGS=$(docker images -q)
# [ ! -z "${IMGS}" ] && docker rmi -f ${IMGS}

source "${SCRIPT_DIR}/opts.sh"

# Build docker image conditionally
if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" > /dev/null 2>&1; then
    echo "Image ${IMAGE_NAME}:${IMAGE_TAG} already exists. Skipping build."
else
    echo "Image ${IMAGE_NAME}:${IMAGE_TAG} not found. Building..."
    ./docker_build.sh
fi

# Check if container is already used
USED_CONTAINER=$(docker ps -a --format '{{.Names}}' | grep -w ${IMAGE_NAME}) || true

if [ ! -z "${USED_CONTAINER}" ];
then
    docker stop --time 2 $USED_CONTAINER > /dev/null 2>&1 || true
    docker rm $USED_CONTAINER > /dev/null 2>&1 || true
fi

# Run test app
if [ "$OR_GPU_SUPPORT" = "1" ];
then
    docker run --privileged \
        --name=open_recon_server -p 9002:9002 \
        --gpus all \
        --stop-timeout 2 \
        -e OR_MODULE="${OR_MODULE}" \
        ${IMAGE_NAME}:${IMAGE_TAG}
else
    docker run --privileged \
        --name=open_recon_server -p 9002:9002 \
        --stop-timeout 2 \
        -e OR_MODULE="${OR_MODULE}" \
        ${IMAGE_NAME}:${IMAGE_TAG}
fi

# to list all created
# docker images

# Check ports:
# docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}"
# Stop container:
# docker stop <name>
# docker rm <name>
