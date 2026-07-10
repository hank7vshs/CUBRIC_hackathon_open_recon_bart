#!/bin/bash
set -e

# Rebuild the CA certificate bundle first.
# The devcontainer.json mounts host SSL certs into /usr/local/share/ca-certificates
# at container start, but update-ca-certificates only runs in postStartCommand —
# which is AFTER postCreateCommand. Without this, git clone fails with
# "server certificate verification failed. CAfile: none".
sudo update-ca-certificates

# Install dependencies for BART
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends make gcc git libfftw3-dev liblapacke-dev libpng-dev libopenblas-dev libgtk-3-dev


# Clone and build BART if not already present
if [ ! -d "/container/bart" ]; then
    git clone https://github.com/mrirecon/bart.git /container/bart
fi

cd /container/bart
git checkout v0.9.00
CUDA=${OR_GPU_SUPPORT:-0} CUDA_BASE=/usr/local/cuda/ CUDA_LIB=lib64 make -j12 all --silent
./bart version -V

# Install bart-view
sudo apt-get install -y bart-view

# Set environment variables for BART system-wide (readable by all shells and VS Code)
sudo bash -c 'echo "BART_TOOLBOX_PATH=/container/bart" >> /etc/environment'
sudo bash -c 'echo "TOOLBOX_PATH=/container/bart"      >> /etc/environment'
sudo bash -c 'echo "OMP_NUM_THREADS=1"                 >> /etc/environment'

# Also add to /etc/profile.d so PATH is updated for interactive and login shells
sudo bash -c 'echo "export PATH=/container/bart:\$PATH" > /etc/profile.d/bart.sh'
sudo bash -c 'chmod +x /etc/profile.d/bart.sh'

# Belt-and-suspenders: also add to ~/.bashrc for interactive terminals
echo 'export BART_TOOLBOX_PATH=/container/bart' >> ~/.bashrc
echo 'export TOOLBOX_PATH=/container/bart'      >> ~/.bashrc
echo 'export OMP_NUM_THREADS=1'                 >> ~/.bashrc
echo 'export PATH="/container/bart:$PATH"'      >> ~/.bashrc