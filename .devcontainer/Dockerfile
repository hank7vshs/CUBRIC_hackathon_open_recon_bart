FROM python:3.11-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# Select desired Open Recon version
ARG OPENRECON=BASELINE

# Required for Docker-in-Docker (DinD) to specify API version for compatibility with older Docker versions on VA60 Baseline
ENV DOCKER_API_VERSION=1.43

# GPU support: set via build.args in devcontainer.json ("0" = off, "1" = on)
ARG OR_GPU_SUPPORT=0
ENV OR_GPU_SUPPORT=${OR_GPU_SUPPORT}

# ----------------------------------
#           Dependencies
# ----------------------------------

RUN pip install --upgrade pip

# Python MRD library
RUN pip install h5py==3.12.1 --prefer-binary
RUN pip install ismrmrd==1.14.1

RUN pip install --no-cache-dir matplotlib==3.9.2 pydicom==3.0.1 numpy==2.4.2 check-jsonschema==0.33.3 pypulseq

# Dependencies
RUN apt-get update -qq && apt-get upgrade -y -qq && apt-get install -qq -y \
    apt-utils gpg man make gcc git git-cola wget vim dpkg unzip screen time bc zip htop tar \
    pandoc texlive-latex-recommended texlive-latex-extra

# Cleanup files
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip

# ----------------------------------
#      ISMRMRD & siemens_to_ismrmrd
# ----------------------------------

RUN apt-get update && apt-get install -y cmake g++ libhdf5-dev libxml2-dev libxslt1-dev libboost-all-dev libfftw3-dev libpugixml-dev
RUN mkdir -p /opt/code

# ISMRMRD library
RUN cd /opt/code && \
    git clone https://github.com/ismrmrd/ismrmrd.git && \
    cd ismrmrd && \
    git checkout d364e03 && \
    mkdir build && \
    cd build && \
    cmake ../ && \
    make -j $(nproc) && \
    make install

# siemens_to_ismrmrd converter
RUN cd /opt/code && \
    git clone https://github.com/ismrmrd/siemens_to_ismrmrd.git && \
    cd siemens_to_ismrmrd && \
    git checkout v1.2.11 && \
    mkdir build && \
    cd build && \
    cmake ../ && \
    make -j $(nproc) && \
    make install

# ----------------------------------
#               Docker
# ----------------------------------
RUN apt-get update -qq && apt-get install -y ca-certificates curl
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN if [ "$OPENRECON" = "BASELINE" ]; then \
        echo "Install Docker for Open Recon on VA60 Baseline..." && \
        VERSION_STRING=5:24.0.0-1~debian.11~bullseye && \
        apt-get update -qq && apt-get -qq -y install docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin; \
    else \
        echo "Install latest Docker version..." && \
        apt-get update -qq && apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin; \
    fi


# ----------------------------------
#               CUDA
# ----------------------------------

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

# Verify CUDA installation
RUN if [ "$OR_GPU_SUPPORT" = "1" ]; then \
        echo "Verifying CUDA installation..." && \
        nvcc --version || echo "nvcc not found"; \
    fi

# Install Nvidia Container Toolkit for DinD with GPU
RUN if [ "$OR_GPU_SUPPORT" = "1" ]; then \
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
        apt-get update && \
        apt-get install -y -qq nvidia-container-toolkit; \
    fi

# Create user and add to sudoers
#   ___________                 ,,,           ___________
#  | . . . . . |              .'    `/\_/\   |  __  __  |
#  | . . . . . |            .'       <@I@>   | (  \/ *) | 
#  | . . + . . | <((((((((((  )____(  \./    |  \   */  |
#  | . . . . . |           \( \(   \(\(      |   \ /    |
#  -------------             `-"`-"  " "     ------------
ARG USERNAME=recoon
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # Add sudo support.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Add user to docker group    
RUN usermod -aG docker $USERNAME

# Set the default user
USER $USERNAME

# Copy the rest of the project files
# --chown is required: COPY defaults to root:root ownership regardless of the
# active USER, which would otherwise block recoon from reading/writing test
# data, out.h5, etc. at runtime.
WORKDIR /container
COPY --chown=$USERNAME:$USERNAME . /container

# In case Git for Windows changed line endings, fix them here
RUN find /container -type f -name "*.sh" -exec chmod +x {} \;
RUN find /container -type f -name "*.sh" -exec sed -i 's/\r$//' {} \;

# Default shell
CMD ["bash"]
