#!/bin/bash
# Reference commands for the guided manual-install walkthrough.
#
# NOT wired into devcontainer.json / install_extra.sh and NOT run automatically.
# Students run these by hand, one section at a time, inside a terminal attached
# to the running devcontainer -- this is a teaching exercise, not automation.
#
# Tested and confirmed working against:
#   .devcontainer/Dockerfile (python:3.11-slim-bullseye / Debian bullseye)

set -e

# ----------------------------------
#        GitHub Copilot CLI
# ----------------------------------
curl -fsSL https://gh.io/copilot-install | sudo bash

# ----------------------------------
#      MRtrix3 (build from source)
# ----------------------------------

# Install dependencies for MRtrix3 (command-line tools only, no Qt GUI)
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends libeigen3-dev zlib1g-dev

# Clone and build MRtrix3 if not already present
if [ ! -d "/container/mrtrix3" ]; then
    git clone https://github.com/MRtrix3/mrtrix3.git /container/mrtrix3
fi

cd /container/mrtrix3
git checkout 3.0.8
./configure -nogui
NUMBER_OF_PROCESSORS=$(nproc) ./build
./bin/mrconvert --version

# Set environment variables for MRtrix3 system-wide (readable by all shells and VS Code)
sudo bash -c 'echo "MRTRIX3_PATH=/container/mrtrix3" >> /etc/environment'

# Also add to /etc/profile.d so PATH is updated for interactive and login shells
sudo bash -c 'echo "export PATH=/container/mrtrix3/bin:\$PATH" > /etc/profile.d/mrtrix3.sh'
sudo bash -c 'chmod +x /etc/profile.d/mrtrix3.sh'

# Belt-and-suspenders: also add to ~/.bashrc for interactive terminals
echo 'export MRTRIX3_PATH=/container/mrtrix3'      >> ~/.bashrc
echo 'export PATH="/container/mrtrix3/bin:$PATH"'  >> ~/.bashrc

# NOTE: after running the MRtrix3 section above, PATH changes only apply to
# NEW shells. In the same terminal, run `source ~/.bashrc` (or open a fresh
# terminal) before calling `mrconvert`/`mrdenoise`/etc.


# installing Supervised_RNS_dMRI package from GitHub with all dependencies as importable module
# because it is not available on PyPI, we install it directly from GitHub using pip.
# luckily, it includes a pyproject.toml file, so pip will automatically install all dependencies listed there.
# we need to add the local bin directory to PATH so that the package's command-line tools are available in the shell
# This will not be necessary for the final server implementation, as it will not have users but only root
# access, and the package will be installed system-wide.
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends build-essential
pip install --no-cache-dir git+https://github.com/Bradley-Karat/Supervised_RNS_dMRI.git

# Non-root pip falls back to a --user install (no write access to system
# site-packages), landing console scripts in ~/.local/bin instead of a
# directory already on PATH. Export now for this shell, and persist to
# ~/.bashrc (matching the MRtrix3 pattern above) so future shells pick it
# up too -- without this, ~/.local/bin is lost the moment this terminal closes.
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc