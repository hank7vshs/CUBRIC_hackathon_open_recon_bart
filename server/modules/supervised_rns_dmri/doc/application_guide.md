# Supervised RNS dMRI App in Open Recon

## Introduction
This guide describes deployment and use of a Docker container that fits diffusion MRI models using supervised machine learning trained with Realistic Noise Synthesis ([Supervised_RNS_dMRI](https://github.com/Bradley-Karat/Supervised_RNS_dMRI)), running within the Open Recon framework by Siemens Healthineers. It is intended for users involved in MRI reconstruction research and development.

## Glossary
### Acronyms
* dMRI – Diffusion Magnetic Resonance Imaging
* RNS – Realistic Noise Synthesis
* MRI – Magnetic Resonance Imaging
* CLI – Command Line Interface
* DICOM – Digital Imaging and Communications in Medicine

### Symbols
* `>` – Indicates a command to be entered in the terminal
* `[...]` – Placeholder for user-specified values

## Indications of Use
This application is intended for research use only. It facilitates diffusion MRI model fitting using a supervised machine learning model trained offline with realistic noise synthesis, integrated into the Open Recon Application.

## Safety Considerations
### Definitions
* `Caution` – Indicates a potential hazard that could result in minor or moderate injury or equipment damage.

### List of Cautions
* Ensure Docker is installed and running before launching the container.
* Do not use this application for clinical diagnosis or patient care.

## Device Description
The application consists of a Docker container that encapsulates the Supervised_RNS_dMRI toolbox and its dependencies, together with a pre-trained model. It interfaces with the Open Recon Application to fit diffusion models to reconstructed DWI images.

## Installation
Follow the instructions provided in the repository root `Readme.md`.

## Instructions For Use
1. Update `supervised_rns_dmri.py` with the model-fitting pipeline (see the TODOs in `_process_image_impl`).
2. Update `application_guide.md` to describe the finished application.
3. Update `appl_spec.json` to match the final set of UI parameters.
4. Run the `create_archive.sh` script and install the generated *.zip file at the scanner.

## Compatibility
* Compatible with Linux and Windows systems with Docker installed.
* Requires Open Recon Application version ...

## Limitations
* Not intended for clinical use.
* Model fitting only -- training happens offline; this container does not retrain the model at runtime.

## Troubleshooting
| Issue                  | Solution                                                   |
| --------               | -------                                                    |
| Container won't start  | Ensure Docker is running and image is correctly pulled     |
| Model artifacts not found | Verify the trained model files are present under `model/` in the image |
| Data not processed     | Check input format and file paths                          |

## Customer Support
For technical support, contact XXX at
* E-mail: this-is-an@example.com
* Phone: +49 123 456789

## Appendix
* Supervised_RNS_dMRI: https://github.com/Bradley-Karat/Supervised_RNS_dMRI
* Docker Documentation: https://docs.docker.com
