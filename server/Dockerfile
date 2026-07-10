# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

FROM python:3.12-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

ARG OR_MODULE
ENV OR_MODULE=${OR_MODULE}

# GPU support: passed via --build-arg from docker_build.sh ("0" = off, "1" = on)
ARG OR_GPU_SUPPORT=0
ENV OR_GPU_SUPPORT=${OR_GPU_SUPPORT}

# Install build dependencies
RUN apt-get update -qq && apt-get upgrade -y -qq && \
    apt-get install -y --no-install-recommends      \
    vim sudo gpg curl build-essential apt-utils          \
    make git bc vim nano libfftw3-dev libblas-dev libpng-dev gcc liblapacke-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Versions are pinned to match the host environment exactly so that numerical results (FFT, array ops) are bit-identical and the shared reference files in test/ref/ remain valid for both test_server.sh and test_docker.sh.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir "numpy==2.4.2" "matplotlib==3.10.8" ismrmrd

# Add key for CUDA installation
RUN if [ "$OR_GPU_SUPPORT" = "1" ]; then \
        mkdir -p /etc/apt/keyrings && \
        curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/3bf863cc.pub | gpg --dearmor -o /etc/apt/keyrings/cuda-archive-keyring.gpg && \
        echo "deb [signed-by=/etc/apt/keyrings/cuda-archive-keyring.gpg] https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64 /" > /etc/apt/sources.list.d/cuda.list; \
    fi

# Force APT to prefer packages from NVIDIA's repo and install CUDA toolkit
RUN if [ "$OR_GPU_SUPPORT" = "1" ]; then \
        echo "Package: *\nPin: origin developer.download.nvidia.com\nPin-Priority: 1001" > /etc/apt/preferences.d/cuda && \
        apt-get update && apt-get install -y --no-install-recommends \
        cuda-toolkit-11-6 && \
        apt-get clean && rm -rf /var/lib/apt/lists/*; \
    fi

# Set environment variables
ENV PATH=/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}

# Verify CUDA installation and clean up
RUN if [ "$OR_GPU_SUPPORT" = "1" ]; then \
        echo "Verifying CUDA installation..." && \
        nvcc --version || echo "nvcc not found" \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Add NVIDIA Container Toolkit labels so --runtime=nvidia works
ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Clone BART
# Update to https://codeberg.org/mrirecon/bart.git/ in the future
RUN git clone https://github.com/mrirecon/bart.git /bart
WORKDIR /bart

# Set environment variables for BART
ENV BART_TOOLBOX_PATH=/bart
ENV TOOLBOX_PATH=/bart
ENV OMP_NUM_THREADS=1
ENV PATH="/bart:$PATH"

# Build BART
RUN git checkout v0.9.00
RUN CUDA=${OR_GPU_SUPPORT} CUDA_BASE=/usr/local/cuda/ CUDA_LIB=lib64 make -j12 all --silent
RUN ./bart version -V

# Copy application code
WORKDIR /opt/code/python-ismrmrd-server
COPY . /opt/code/python-ismrmrd-server

# ----------------------------------
#               Server Config
# ----------------------------------

# ENTRYPOINT ["python3", "/opt/code/python-ismrmrd-server/server.py"]

CMD [ "/bin/bash", "-c", "/sbin/ldconfig && exec python3 /opt/code/python-ismrmrd-server/server.py --or-module ${OR_MODULE}" ]
