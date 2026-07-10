# Open Recon Examples

- [Open Recon Examples](#open-recon-examples)
  - [Target Group](#target-group)
  - [Idea of the Tutorial](#idea-of-the-tutorial)
  - [Dependencies and Setup](#dependencies-and-setup)
    - [Prerequisites: Common Requirements (Windows \& Linux)](#prerequisites-common-requirements-windows--linux)
    - [Windows-Specific Setup](#windows-specific-setup)
      - [Check Version of Windows](#check-version-of-windows)
      - [Install WSL](#install-wsl)
      - [Install Docker Desktop](#install-docker-desktop)
    - [Linux-Specific Setup](#linux-specific-setup)
    - [Starting a Session](#starting-a-session)
  - [Run the Python Server Scripts](#run-the-python-server-scripts)
    - [`r2ci_bart` — Raw k-space to Complex Image](#r2ci_bart--raw-k-space-to-complex-image)
    - [`i2i_invertcontrast` — Image-to-Image Contrast Inversion](#i2i_invertcontrast--image-to-image-contrast-inversion)
    - [Switching Modules](#switching-modules)
  - [Perform the Reconstruction in a Docker Container](#perform-the-reconstruction-in-a-docker-container)
  - [Add Your Own Reconstruction](#add-your-own-reconstruction)
  - [Define Config and Application Manual](#define-config-and-application-manual)
  - [Generate an OpenRecon Compressed Archive](#generate-an-openrecon-compressed-archive)
  - [Deploy the OpenRecon Archive at the Scanner](#deploy-the-openrecon-archive-at-the-scanner)
    - [Installation](#installation)
    - [Verify Successful Installation](#verify-successful-installation)
    - [On-Scanner Debug Tips](#on-scanner-debug-tips)
      - [General Config](#general-config)
      - [Inspect the local Docker registry](#inspect-the-local-docker-registry)
      - [Run the Docker container manually](#run-the-docker-container-manually)
  - [Inspect installed OpenRecon applications](#inspect-installed-openrecon-applications)
  - [Develop Your Own Applications With This Repository](#develop-your-own-applications-with-this-repository)
    - [Library](#library)
    - [Testing](#testing)
    - [GPU Usage](#gpu-usage)
    - [Quickstart (VS Code Debug)](#quickstart-vs-code-debug)
  - [Further Materials](#further-materials)
  - [AI Coding Agents](#ai-coding-agents)
    - [Available Agents](#available-agents)
    - [When and How to Use the Agents](#when-and-how-to-use-the-agents)
    - [Getting the Most Out of the Agents](#getting-the-most-out-of-the-agents)
    - [Model Selection and Limitations](#model-selection-and-limitations)
    - [Verification Commands](#verification-commands)
  - [FAQ](#faq)
      - [How to avoid the error "Dockerx Not Found"?](#how-to-avoid-the-error-dockerx-not-found)
      - [Why do I not receive any visual output when running `python3 display.py out.h5`?](#why-do-i-not-receive-any-visual-output-when-running-python3-displaypy-outh5)
      - [How to resolve the error that a container with ID CONTAINER-ID cannot be built?](#how-to-resolve-the-error-that-a-container-with-id-container-id-cannot-be-built)
  - [Disclaimer](#disclaimer)

## Target Group
The target group of this tutorial is everyone who is interested in running their own custom reconstructions on a Siemens Healthineers MRI scanner with VA60.
The basis for this simple example is a Python server calling the Berkeley Advanced Reconstruction Toolbox ([BART](https://mrirecon.github.io/bart/)), which provides many powerful but easy-to-use tools for MRI reconstructions.
The tutorial requires basic knowledge of Python development. It is beneficial if you are already familiar with BART's Python or shell interface. If not, we recommend looking into the [BART tutorials](https://mrirecon.github.io/bart/tutorials.html), and especially:
* Introduction to BART and Its Shell Interface: [BART workshop - ISMRM 2019](https://github.com/mrirecon/bart-workshop/blob/master/ismrm2019/intro/intro.ipynb)
* Introduction to BART and Its Shell Interface: [ESMRMB MRI-Together 2021 workshop](https://github.com/mrirecon/bart-workshop/tree/master/mri_together_2021)
* Introduction to BART and Python: [Webinar for new users - Python](https://github.com/mrirecon/bart-webinars/tree/master/webinar4)

If you have questions about BART tools, reconstruction algorithms, or its Python interface, you can also ask the built-in [`@bart-toolbox`](#available-agents) agent directly in the VS Code Copilot Chat.

## Idea of the Tutorial
This work provides a recipe for running your own reconstruction on a Siemens Healthineers scanner with Open Recon under VA60.
It offers an explanation and efficient workflow for generating the required archives based on a simple Python server.
In its current form, this repository allows you to modify the code easily and extend it to include your custom reconstructions.
Recommendations for developing your own work in this repository can be found in section [Develop Your Own Applications With This Repository](#develop-your-own-applications-with-this-repository).

This tutorial is set up in a development container to provide a tool for designing your own online reconstructions. With this approach, most of the complexity of packaging an Open Recon container on VA60 is encapsulated and automated with various scripts. The development container comes with a Docker-in-Docker solution to support the required older Docker versions as well as the old CUDA version for running your reconstructions on MaRS' GPUs (MaRS is the server at the scanner running the reconstructions and it is equipped with a dedicated GPU; see section [GPU Usage](#gpu-usage)).

If you are new to Docker or the Open Recon application specification format, the [`further_materials/`](further_materials) folder contains standalone tutorials that cover these topics in depth. You can work through them at any point — they are independent of the main tutorial flow.

## Dependencies and Setup
The dev-container environment requires some preparation. In the following, you can find instructions on the required programs and setup steps.
Ensure to execute the steps in the order in which they are listed here to avoid additional debugging.
If issues occur, please check out the [FAQ](#faq) section for a list of known potential difficulties and errors.

Installation steps are listed for Windows and Linux only. macOS systems should work similarly — feel free to try it out and provide feedback to improve this documentation in future revisions.

### Prerequisites: Common Requirements (Windows & Linux)
Please install the following requirements first:
* **Visual Studio Code**: Download from https://code.visualstudio.com or install via the Windows Store. If you are not already familiar with this IDE, we recommend going through the official introductory materials at https://code.visualstudio.com/docs/introvideos/basics.
* **Dev Containers Extension** in VS Code: Open the VS Code extension marketplace and install **Dev Containers** (id: `ms-vscode-remote.remote-containers`). This extension enables working inside the Docker-based virtual environment as if you were developing locally.

### Windows-Specific Setup
#### Check Version of Windows
If you run this tutorial on a Windows machine ensure that your computer can run Docker Desktop. More details on this can be found at the official Docker Desktop support page: https://docs.docker.com/desktop/setup/install/windows-install/.
#### Install WSL
The development with devcontainer under Windows requires to install the Windows Subsystem for Linux 2 (WSL 2). It adds an app with a virtual machine running linux to your operating system which is tightly integrated into the Windows operating system. From experience, it is important to install WSL 2 by executing:
```powershell
wsl --install
```
in your **powershell**. Afterwards, you can enter
```powershell
wsl
```
and are entering the linux machine from the command line. You can print out information about your linux distribution by entering
```bash
cat /etc/os-release
```
#### Install Docker Desktop
After verifying that WSL is installed and runs properly [Docker Desktop](https://www.docker.com/products/docker-desktop) needs to be installed. Download the program from its official website and install it. **You do not need to sign up here!** Ensure that the WSL integration for Docker Desktop is turned on. You can find it at: `Settings` -> `general` -> `Use the WSL 2 based engine`. After the installation reboot your computer.

Following the restart, you can verify the accessibility of Docker from within the WSL. First, start Docker Desktop. This starts the Docker daemon, which needs to be accessible from within the WSL. The running daemon is indicated in the hidden icon section of your taskbar by a whale carrying containers. Hovering over it tells you in a pop-up window that it is running. Next, open a powershell, go into your WSL by executing
```powershell
wsl
```
and run the command
```bash
docker --version
```
This should provide you with output similar to `Docker version 28.4.0, build d8eb465`, but most likely with a different version. For us it is important that it printed output at all. This means docker is accessible from within your WSL.

This finalizes the Windows specific setup. Jump to [Starting a Session](#starting-a-session) to continue.


### Linux-Specific Setup
1. Install Docker (https://docs.docker.com/engine/install/). Follow the instructions for your distribution. For Ubuntu, paste the following into your terminal:
```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
2. Add your user to the Docker group:
```bash
sudo usermod -aG docker $USER
```
3. Enable and start Docker:
```bash
sudo systemctl enable docker
sudo systemctl start docker
```

### Starting a Session
First, start Docker — either Docker Desktop on Windows or the Docker daemon on Linux.
The Docker daemon must be running before proceeding.

Next, open the folder of this repository in VS Code. You can either open it from the VS Code GUI or navigate to the repository folder in your terminal (or WSL on Windows) and run `code .`.

After confirming that you trust the workspace (shown only the first time), a pop-up will appear in the bottom-right corner of VS Code asking if you want to re-open the project in a devcontainer. Select **Re-open in Container**.

This automatically builds a Docker container from the files in the `.devcontainer` folder:
```
├── .devcontainer/
│   ├── certs/
│   ├── Dockerfile
│   ├── Readme.md
│   ├── devcontainer.json
│   └── install_extra.sh
```
The container provides all dependencies (Docker 24.0.0, CUDA 11.6, BART, Python packages) required for Open Recon on VA60, without any manual setup on your host machine.

> **First-time build**: Creating the devcontainer for the first time takes several minutes, as it builds the Docker image and compiles BART from source. Subsequent starts reuse the existing container and are much faster.

When finished, the VS Code session starts inside the container and you can continue with this tutorial.

## Run the Python Server Scripts

On a real scanner, Open Recon streams MRI data to the reconstruction server over TCP in real time — the server processes it and sends the result back over the same connection. The test client simulates this by reading from an `.h5` file and streaming it the same way. This is why the server and client run in **two separate terminals**.

The server supports two modules; start with `r2ci_bart` for a BART-based reconstruction.

**Terminal 1 — Server:**
```bash
cd server
./run_server.sh r2ci_bart
```

**Terminal 2 — Client:**
```bash
cd client
./run_client.sh
python3 display.py out.h5
```

For the other module `i2i_invertcontrast`, pass its name to:
- `./run_server.sh i2i_invertcontrast` — contrast inversion on pre-reconstructed images
- `./run_client.sh i2i_invertcontrast` — load data for inversion on pre-reconstructed images

See [`server/Readme.md`](server/Readme.md) for details on all modules and [`client/Readme.md`](client/Readme.md) for how to select input datasets.

### `r2ci_bart` — Raw k-space to Complex Image

The default pipeline. Raw k-space is emitted from ICE (the scanner's inline image reconstruction pipeline) after noise pre-whitening, reconstructed by BART (`ecalib` + `pics`), and the complex image is injected back into ICE — **replacing the Fourier transform step**. The terms "emitter" and "injector" describe where in ICE the data leaves and re-enters; these are configured in [`appl_spec.json`](further_materials/02_VA60_application_specification_tutorial).

See [`server/modules/r2ci_bart/Readme.md`](server/modules/r2ci_bart/Readme.md) for the full pipeline description, UI parameters, and customization guide.

### `i2i_invertcontrast` — Image-to-Image Contrast Inversion

A minimal example with no BART dependency. Pre-reconstructed magnitude images are received from ICE (the scanner has already performed its standard reconstruction) and returned with inverted contrast ($\text{output} = \text{maxVal} - \text{input}$). Use this as a starting template for image-to-image modules.

See [`server/modules/i2i_invertcontrast/Readme.md`](server/modules/i2i_invertcontrast/Readme.md) for details.

### Switching Modules

The default module is controlled by the environment variable `OR_MODULE`. You can pass a different module name directly to `run_server.sh` (as shown above), or change the default by editing [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json):

```json
"containerEnv": {
    "OR_MODULE": "i2i_invertcontrast"
},
```

After changing this value, rebuild the devcontainer: open the VS Code command palette (`Ctrl+Shift+P`) and select **Dev Containers: Rebuild Container**. This default is also used by `docker_build.sh` and `create_archive.sh` when packaging for the scanner.

## Perform the Reconstruction in a Docker Container

The previous section ran the Python server directly inside the devcontainer. On the scanner, your code runs inside a Docker container — so this section verifies that it works the same way in the **Open Recon Docker image** that will actually be deployed.

**Server**</br>
In terminal 1, navigate to the `server` folder and run:
```bash
cd server
./run_docker.sh r2ci_bart
```
This builds the Open Recon Docker image (if not already present) and starts the Python server inside it. The `r2ci_bart`/`i2i_invertcontrast` argument is supported here exactly as with `run_server.sh`.

**Client**</br>
In terminal 2, navigate to the `client` folder and run the client as before:
```bash
cd client
./run_client.sh
```
Visualize the result:
```bash
python3 display.py out.h5
```

## Add Your Own Reconstruction

The core BART reconstruction is in [`server/modules/r2ci_bart/r2ci_bart.py`](server/modules/r2ci_bart/r2ci_bart.py). The two key lines are:

```python
sens = bart.bart(1, 'ecalib -m 1', kspace_cut)
reco = bart.bart(1, 'pics ' + str(pics_flags), kspace_cut, sens)
```

Replace or extend these with any BART command or custom Python code. For a step-by-step guide including how to add UI parameters and tests, see [`server/modules/r2ci_bart/Readme.md`](server/modules/r2ci_bart/Readme.md).

If you want to create an entirely new module, the [`@new-module`](#available-agents) agent can guide you through the full process — from scaffolding the directory to writing `process()`, configuring `appl_spec.json`, and adding tests. See [AI Coding Agents](#ai-coding-agents) for more details.

## Define Config and Application Manual
Each module's `doc/` folder contains `appl_spec.json` (scanner UI parameters and metadata) and `application_guide.md` (application description). The `appl_spec.json` controls how the scanner presents your reconstruction to the operator — which UI fields appear, what workflow type is used, and what metadata identifies your application. See the [application specification tutorial](further_materials/02_VA60_application_specification_tutorial) for a detailed walkthrough.

Update these files when you add new parameters or change the module's purpose. See the module `Readme.md` files for details on the `appl_spec.json` schema and validation.
You can validate the `appl_spec.json` schema with:
```bash
check-jsonschema --schemafile server/modules/r2ci_bart/doc/appl_spec_schema.json server/modules/r2ci_bart/doc/appl_spec.json
```

## Generate an OpenRecon Compressed Archive
OpenRecon requires a specific archive format for importing containers at the scanner. The default format targets VA60; for VA70+ scanners, an Alpaca package format is also supported — see the [packaging guide](further_materials/03_packaging_guide) for details on the differences.
The two most important files are the **configuration** (e.g. [`server/modules/r2ci_bart/doc/appl_spec.json`](server/modules/r2ci_bart/doc/appl_spec.json)) and the [**Application Guide**](server/modules/r2ci_bart/doc/application_guide.md) — both live under the selected module's `doc/` folder.

**Before generating the archive, set the active module** in [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json):
```dockerfile
    "containerEnv": {
        "OR_MODULE": "r2ci_bart"
    },
```
If a different module is to be used, replace `r2ci_bart` with the respective package name and rebuild the devcontainer for the change to take effect (open the VS Code command palette with `Ctrl+Shift+P` and select **Dev Containers: Rebuild Container**). `server/docker_build.sh` and `create_archive.sh` read the devcontainer environment variable to build the image with the correct default module, locate the right `doc/` folder and embed the respective `appl_spec.json` into the Docker image.

From the root directory of the repository, run:
```bash
./create_archive.sh              # VA60 (default)
./create_archive.sh --va70       # VA70+ Alpaca package format
./create_archive.sh --va70 --oci # VA70+ with OCI-layout export
```
This script automatically:
1. Locates `server/modules/<OR_MODULE>/doc/`
2. Validates `appl_spec.json` against the schema
3. Generates a PDF from `application_guide.md`
4. Builds the Docker image and packages everything into a zip archive
5. (VA70+ only) Generates `ApplSpec.json` and `Properties.json` for the Alpaca package format

The output filename is derived from `appl_spec.json` fields (vendor, id, version). With the default `r2ci_bart` config it produces:
- VA60: `OpenRecon_SHSTeam_OpenReconR2CI_V1.0.0.zip`
- VA70+: `OpenRecon_SHSTeam_OpenReconR2CI_V1.0.0.OpenReconPackage.zip`

## Deploy the OpenRecon Archive at the Scanner

Transfer the generated compressed archive zip file (e.g. `OpenRecon_SHSTeam_OpenReconR2CI_V1.0.0.zip`) to the VA60 scanner and follow the steps below.

### Installation

1. **Exit the scanner's kiosk interface** using the key combination: "`Tab` + `Del` + `NUM` + `+`". This might require to login administrator (`medadmin`). The same key combination returns you to kiosk mode afterwards.

2. **Copy the zip file** to the OpenRecon installer inbox on the scanner:
    ```
    C:\Program Files\Siemens\Numaris\OperationalManagement\FileTransfer\incoming
    ```
   You might be required to copy the files first from your drive to the system (e.g. to `K:\Temp`) and afterwards to the installation folder above. Additionally, you might be prompted to perform this action with admin rights: `medadmin` user and password.

3. **Run the installer** The installation starts automatically once the file is placed in that folder. There is no progress dialog — the zip file is silently removed from the folder once processing starts, but installation may still be ongoing at that point. Allow a few minutes before checking the result.

### Verify Successful Installation

1. Open the **MyExam Cockpit** on the scanner and create or edit a program in the exam tree.
2. Add a protocol to the program.
3. Open any sequence and check the **Inline** tab — a successfully installed OpenRecon package adds an **OpenRecon** tab with an **Algorithm** dropdown (default value: `None`).

**Alternative Solutions**

1. **Monitor using Logs**  
    OpenRecon package installation related logs can be found at:
    ```
    C:\ProgramData\Siemens\Numaris\log\syngo.MR.HostInfra.OpenRecon.Watcher
    ```
    open the corresponding files using the `logviewer` application.
2. **Monitor via Administrator Portal**:
     1. Select `Configuration`
     2. `Administrator Portal`
     3. Enter `medadmin` credentials
     4. Select `Open Message Viewer`
     5. Search for Message Text `OpenRecon` to find all messages
3. You can inspect the json file collecting all OpenRecon installations on a system. See [Inspect installed OpenRecon applications](#inspect-installed-openrecon-applications) for more information.

### On-Scanner Debug Tips

#### General Config
OpenRecon provides a general configuration file located at:
```
C:\Program Files\Siemens\Numaris\MriProduct\Ice\IceConfigurators\OpenRecon\OR.Default.GeneralConfig.json
```
This file provides the option to disable checks for High-Performance MaRS, HPC (High-Performance Computing cluster), and other functionality that is turned on by default. It allows the user to debug generic applications that might be limited by these checks.

#### Inspect the local Docker registry
Installed OpenRecon images can be inspected from the host Windows machine (not the MaRS!). The required tool is `crane` and has been pre-installed on the system.

You can list all installed images using:
```bash
crane catalog localhost:37001
```
Here, the port 37001 is the default for VA60 systems. For VB10 onwards it is 42441.
The command provides you with the information about the installed images similar to `localhost:37001/openrecon/shs/subtraction`.

Afterwards, you can inspect the installed version of that image (here with `<image-name>`=`subtraction`) with
```bash
crane ls localhost:37001/openrecon/shs/subtraction
```
The list contains all versions as specified in the appl_spec.json files of the installed OR applications: `1.0.0`.
The sha of the specific container can then be accessed using:
```bash
crane digest localhost:37001/openrecon/shs/subtraction:1.0.0
```
and the label can be extracted with 
```bash
crane config localhost:37001/openrecon/shs/subtractionlinkedjobspec:1.0.0
```

#### Run the Docker container manually
Running an OpenRecon container manually requires to set the general config entry `selectedimagehostcontrollername` in the json file: `C:\Program Files\Siemens\Numaris\MriProduct\Ice\IceConfigurators\OpenRecon\OR.Default.GeneralConfig.json` from the default `"Docker"` to `"manual"`. 
This requires you to start the OpenRecon docker container manually from the MaRS. You can SSH into MaRS using the MARS_SSH client and run the command:
```bash
docker run -p 9002:9002 --gpus all --privileged <image-name>:<version>
```
Replace `<image-name>:<version>` with the actual image reference from the local registry. You can find it using the `crane` commands from the previous section — for example, `localhost:37001/openrecon/shs/subtraction:1.0.0`. Alternatively, run `docker images` on MaRS to list available images.

Here, the port 9002 is the default port on which the container receives the data and sends the processed result back.

## Inspect installed OpenRecon applications
Because the installation process of OpenRecon does not provide you with direct feedback about the installation process, it comes in handy to check all installed OR applications. They are added to the JSON file `OpenReconStore.json` located at:
```
C:\ProgramData\Siemens\Numaris\MriSiteData\Scanner\OpenReconStore.json
```
Modifying this file and reloading protocols at the scanner gives you direct access to inspect and test changes to the UI parameters and reconstruction settings of your OpenRecon application avoiding a full reinstallation.

## Develop Your Own Applications With This Repository
### Library
This repository contains the infrastructure needed to develop your own OpenRecon applications.
Shared server library files are in [`server/src/`](server/src) — this includes the MRD connection handler (`connection.py`), helper utilities (`mrdhelper.py`), and protocol constants (`constants.py`). See [`server/Readme.md`](server/Readme.md) for details on each file and the MRD message flow.

Processing modules live in [`server/modules/`](server/modules) — each module is a Python subpackage with an `__init__.py` that exports `process()` and a `doc/` subfolder with `appl_spec.json` and `application_guide.md`.
After completing this tutorial you will know how to modify the BART reconstruction block. Some further options are:
* **Use your own scanner data**: Export a `.dat` file from the scanner console and convert it to ISMRMRD `.h5` using the included [`siemens_to_ismrmrd` conversion tool](further_materials/04_raw_data_conversion). The tutorial includes an example `.dat` file and a script that handles multi-measurement files and validates the output.
* **Design your own BART reconstruction**: BART provides many powerful reconstruction, simulation, and sequence design tools. Use its Python interface, familiarize yourself with BART's syntax, and add your own routines with just a few lines of Python.
* **Write your own Python module**: The module `r2ci_bart` is a good template. Create a new subfolder under `server/modules/`, add an `__init__.py` exporting `process()`, add a `doc/` subfolder with `appl_spec.json` and `application_guide.md`, and register the new module name in the `choices=` list in `server.py`. If you want to use `sigpy`, PyTorch, TensorFlow, or other libraries, add them to `.devcontainer/install_extra.sh` (for the devcontainer) and to `server/Dockerfile` (for the Open Recon container), then rebuild. These are two separate Docker environments — the devcontainer is your development machine, while `server/Dockerfile` defines the image that runs on the scanner — so dependencies must be listed in both.
* **Go beyond Python**: Open Recon is not limited to Python. You can replace the full server with any implementation — the [`05_bash_ncat_server`](further_materials/05_bash_ncat_server) tutorial shows how to build a complete reconstruction server using only bash, socat, and BART, with no Python server at all. The same pattern works as a wrapper for any command-line reconstruction tool. This repository still provides a useful dev-environment that handles Docker-in-Docker, older Docker versions, and CUDA compatibility so you don't have to.

This repository also includes AI coding agents that can help you develop, understand, and document your module — see [AI Coding Agents](#ai-coding-agents) for details.

### Testing
The environment includes a testing framework for the Python server tools and the BART wrapper module. It lets you verify that newly added features do not break existing reconstructions, and that your local dev-environment is set up correctly. The framework is in the [`test/`](test) folder — see its [Readme](test/Readme.md) for detailed instructions.

### GPU Usage
The MaRS GPU running VA60 supports CUDA 11.6. To enable it, set `OR_GPU_SUPPORT` to `"1"` in [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json):

```jsonc
"build": {
    "dockerfile": "Dockerfile",
    "args": {
        "OR_GPU_SUPPORT": "1"
    }
},
```

Also uncomment the GPU passthrough in the same file's `runArgs`:

```jsonc
"runArgs": [
    "--privileged",
    "--gpus", "all"
],
```

The server's Docker image (`server/Dockerfile`) picks up the same setting automatically — `docker_build.sh` forwards `OR_GPU_SUPPORT` as a build argument, and `run_docker.sh` adds `--gpus all` at runtime when the variable is `"1"`.

To test GPU reconstruction locally, your host machine must have:
- A CUDA driver ≥ 11.6
- The [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

Once set up, enable the GPU in BART's `pics` call by adding `-g` to `picsFlagsId` in [`client/debug_ui_data.json`](client/debug_ui_data.json):
```json
"picsFlagsId": "-e -S -g"
```
Then follow the same server/client steps as in the previous sections.

### Quickstart (VS Code Debug)
This section provides a very high-level start. It assumes your VS Code and devcontainer setup is already done.
For setup details, see [Dependencies and Setup](#dependencies-and-setup), especially [Starting a Session](#starting-a-session).

1. Open this repository in VS Code and re-open it in the devcontainer (see [Starting a Session](#starting-a-session)).
2. Open the **Run and Debug** view (`Ctrl+Shift+D`).
3. Select the launch profile **`Server + client`** from the dropdown (defined in [`.vscode/launch.json`](.vscode/launch.json)). This starts the server with the module set in `OR_MODULE` (see [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json)) and runs the client against the demo dataset `test/data/tse_r2ci.h5`.
4. Press **F5** or click the green play button to start.

The output image is written to `client/out.h5`. Display it with:
```bash
cd client && python3 display.py out.h5
```

For the detailed manual terminal-based flow, see [Run the Python Server Scripts](#run-the-python-server-scripts).

## Further Materials

The [`further_materials/`](further_materials) folder contains supplementary hands-on tutorials for key background topics. They run entirely inside the devcontainer and can be completed independently of the main tutorial.

| Tutorial | Description |
|---|---|
| [`01_docker_tutorial`](further_materials/01_docker_tutorial) | Introduction to Docker — images, containers, Dockerfiles, ports, and labels. Work through this if you are unfamiliar with Docker concepts used in this repository. |
| [`02_VA60_application_specification_tutorial`](further_materials/02_VA60_application_specification_tutorial) | How to write and validate an Open Recon `appl_spec.json` — metadata, reconstruction settings (emitter/injector), hardware requirements, and UI parameters. |
| [`03_packaging_guide`](further_materials/03_packaging_guide) | Packaging formats for VA60 (Baseline) and VA70+ (Alpaca) — archive contents, `Properties.json`, image digest extraction, and installation at the scanner. |
| [`04_raw_data_conversion`](further_materials/04_raw_data_conversion) | Convert Siemens `.dat` raw data files to ISMRMRD `.h5` format using `siemens_to_ismrmrd`. Includes an example `.dat` file and a conversion script with built-in validation. |
| [`05_bash_ncat_server`](further_materials/05_bash_ncat_server) | A minimal MRD-compatible reconstruction server using bash, socat, and BART — no Python server needed. Demonstrates that the server pattern is language-agnostic and that any command-line tool can be wrapped behind a TCP socket. |

## AI Coding Agents

This repository includes built-in support for AI coding assistants. If you use VS Code with [GitHub Copilot](https://github.com/features/copilot) (or a compatible agent such as Cursor or Codex), you can talk to **specialized agents** that understand the repository and explain it from the perspective of an MRI researcher who is new to Python servers, Docker, and Open Recon.

[`AGENTS.md`](AGENTS.md) provides the underlying project guidance (layout, build commands, module interface, code style). The agents listed below build on that foundation and give you an interactive, conversational way to learn and work with the codebase.

### Available Agents

The agents live in [`.github/agents/`](.github/agents) and are automatically discovered by VS Code. Select them from the agent picker in the Copilot Chat panel (the `@` menu), or let the default agent delegate to them based on your question.

| Agent | Invoke with | What it does |
|---|---|---|
| **BART Toolbox** | `@bart-toolbox` | Answers questions about the [Berkeley Advanced Reconstruction Toolbox](https://mrirecon.codeberg.page/) — command-line tools, Python interface, reconstruction algorithms (`ecalib`, `pics`, `nufft`), calibration methods, regularization, and how BART is used in this repository. Read-only. |
| **Code Walkthrough** | `@code-walkthrough` | Explains the codebase structure — how `server.py` dispatches to modules, what `connection.py` does, how the `src/` library works. Read-only; won't change files. |
| **New Module** | `@new-module` | Step-by-step guidance for creating your own reconstruction module — from choosing between r2ci and i2i workflows to writing `process()`, configuring `appl_spec.json`, and adding tests. Can edit files and run commands. |
| **Repo Tester** | `@repo-tester` | Runs the full AGENTS.md verification checklist — script syntax, schema validation, host and Docker tests, Docker builds, and all packaging formats. Produces a pass/fail summary table. Can run commands. |
| **Tutorial Reviewer** | `@tutorial-reviewer` | Reviews any documentation from the perspective of the target audience (MRI researcher, new to Docker/Python servers). Provides structured feedback on clarity, assumed knowledge, and learning path. Read-only. |

### When and How to Use the Agents

**Creating your own module** — When you are ready to add your own reconstruction, `@new-module` will guide you through every step:
> "I have a pytorch-based reconstruction located at <path-to-folder>. Help me create a new module for it."

**Getting oriented** — When you first open the repository and want to understand the overall structure, start a Copilot Chat and ask `@code-walkthrough` something like:
> "Walk me through how data flows from the client to the server and back."

**Learning about BART** — If you want to understand a BART tool, its flags, or the MRI algorithm behind it, ask `@bart-toolbox`:
> "What does `bart pics -e -S` do and what regularization options are available?"

**Improving documentation** — If you are writing or editing a Readme and want feedback from the target audience's perspective, ask `@tutorial-reviewer`:
> "Review the root Readme.md — where would a newcomer get stuck?"

**Verifying the repository** — After making changes, ask `@repo-tester` to run the full verification checklist:
> "Test everything."

### Getting the Most Out of the Agents

- **Start broad, then drill down.** Ask a high-level question first ("How does the server work?") and follow up with specifics ("What happens when the last readout in a slice arrives?"). The agents maintain conversation context.
- **Combine agents in one session.** You can switch between agents in the same chat. For example, use `@code-walkthrough` to understand the existing module, then switch to `@new-module` when you are ready to create your own.
- **Use the reviewer before committing documentation changes.** `@tutorial-reviewer` catches assumed knowledge and jargon that is easy to overlook when you are close to the code.
- **Let the agents run commands.** The new-module agent can execute shell commands and edit files. Tell it what you want to achieve and it will run the right scripts.
- **Ask "why", not just "what".** These agents are designed to explain the reasoning behind design decisions — why a TCP server instead of file I/O, why readout oversampling causes a 2× factor, why `appl_spec.json` exists. This context helps you make better decisions in your own module.

### Model Selection and Limitations

The quality of AI agent responses depends significantly on the underlying language model. In general, newer and more capable models produce better, more accurate results. The agents in this repository have been tested with **Claude Opus 4.6** — if your Copilot setup offers a model selection, prefer the most recent available model.

**Important:** Always cross-validate recommendations from any AI agent. Language models can produce incorrect or outdated information — especially for domain-specific topics like MRI reconstruction parameters, BART flags, or scanner-specific behavior. Verify generated code by running the test suite (`test/test_server.sh --speed fast`) and review any suggested configuration changes before applying them.

### Verification Commands

The repository includes ready-made prompt commands that execute and verify specific parts of the tutorial and infrastructure. In the Copilot Chat panel, type `/` to see the available commands, or invoke them directly:

| Command | What it verifies |
|---|---|
| `/verify-scripts` | Shell script syntax (`bash -n`) and `appl_spec.json` schema validation |
| `/verify-tests` | Fast host-mode test suite (`test_server.sh --speed fast`) |
| `/verify-main-tutorial` | Main tutorial end-to-end: server, client, display, schema, tests, Docker |
| `/verify-docker-tutorial` | Docker tutorial (`further_materials/01_docker_tutorial`): all hands-on steps |
| `/verify-appl-spec-tutorial` | Application specification tutorial (`further_materials/02_VA60_application_specification_tutorial`) |
| `/verify-packaging-tutorial` | Packaging guide (`further_materials/03_packaging_guide`): Docker builds and label inspection |
| `/verify-raw-data-tutorial` | Raw data conversion (`further_materials/04_raw_data_conversion`): `.dat` to `.h5` conversion and reconstruction |
| `/verify-bash-server-tutorial` | Bash BART server (`further_materials/05_bash_ncat_server`): socat server, client round-trip, output verification |
| `/verify-packaging` | Archive generation in all formats (VA60, VA70+, VA70+ OCI) with content verification |

These commands live in [`.github/prompts/`](.github/prompts) and are automatically discovered by VS Code. Each command runs the agent with execution permissions, so it will run shell commands, check outputs, and report results.

To run **all** verification steps in sequence, use the [`@repo-tester`](#available-agents) agent — it orchestrates the prompts above and produces a pass/fail summary table.

## FAQ
#### How to avoid the error "Dockerx Not Found"?
* **Error**: On container start, an error occurs that the command `dockerx` is not found.
* **Reproduction**: This error typically accompanies a WSL issue.
  1. Open a *PowerShell*.
  2. Start WSL by running `wsl`.
  3. **Option A**: WSL does not start — it has not been correctly installed. Windows provides multiple ways that appear to install WSL but may not complete it correctly.
  4. **Option B**: WSL starts, but running `docker --version` inside it fails with an error saying Docker cannot be accessed.
* **Solution**: Correctly install WSL by running `wsl --install` from *PowerShell*. Restart your computer and then follow the devcontainer setup instructions again.

#### Why do I not receive any visual output when running `python3 display.py out.h5`?
* **Error**: The Python call executes without error, but no image appears in a pop-up window (or the window is minimized/invisible).
* **Reproduction**: In a bash terminal inside the devcontainer, run `echo $DISPLAY`.
  * **Case 1** — output is empty: The `DISPLAY` variable is not set. This is expected in the provided setup but indicates the X11 forwarding is not configured.
  * **Case 2** — output is `:0`: The variable is set but points to an incorrect display.
* **Solution**: Case 1 typically originates from an incomplete WSL installation. Run `wsl --install` from *PowerShell*, restart, and re-open the devcontainer. Case 2 has been resolved by rebooting the host machine (can be caused by background software installed by an IT department).

#### How to resolve the error that a container with ID CONTAINER-ID cannot be built?
* **Error**: The devcontainer fails to start, reporting that a container with a specific ID cannot be built. This is a subtle error that may depend on your specific setup.
* **Cause**: A container from a previous devcontainer session already exists and is incompatible with the current `devcontainer.json` settings (e.g. after changing mounts or build arguments).
* **Solution**: Remove the conflicting container from a WSL terminal:
  ```bash
  docker container rm -f <CONTAINER-ID>
  ```
  Then rebuild the devcontainer via VS Code: **Command Palette** (`Ctrl+Shift+P`) → `Dev Containers: Rebuild Container`.

## Disclaimer

This repository is provided by Siemens Healthineers AG.
By using this software you acknowledge and agree to the
[Open Recon Terms of Use](https://www.magnetom.net/pub/Open-Recon-ToU).

The Example Code in this repository is licensed under the
[MIT License](LICENSE) (see Section 5.7 of the Terms of Use).

**No warranty.** This software is provided **"as is"**
without any warranty of any kind. Any liability for defects is expressly
excluded (Section 8.1 of the Terms of Use).

**Not for diagnostic use.** All DICOM images created by running container files
on a Siemens Healthineers MR System developed with this application are
labeled "Not for diagnostic use" (Section 8.4 of the Terms of Use).

**Safety and regulatory responsibility.** The developer is solely responsible
for ensuring that the use of container files on humans complies with the
Medical Device Regulation (EU) 2017/745 and all applicable national laws
(Section 8.3 of the Terms of Use). Siemens Healthineers assumes no liability for container files or
for defects resulting from their use (Section 8.4 of the Terms of Use).

**Non-commercial use.** This repository must not be used for
commercialization of developed applications. Additional contracts with
Siemens Healthineers are required for any commercial use (Sections 5.2 & 5.4 of the Terms of Use).