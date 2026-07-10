# BART in Open Recon Application Example

## Introduction
This exemplary guide provides instructions for deploying and using a Docker container that runs the Berkeley Advanced Reconstruction Toolbox (BART) within the Open Recon framework by Siemens Healthineers. It is intended for users involved in MRI reconstruction research and development.

## Glossary
### Acronymns
* BART – Berkeley Advanced Reconstruction Toolbox
* MRI – Magnetic Resonance Imaging
* CLI – Command Line Interface
* API – Application Programming Interface
* DICOM – Digital Imaging and Communications in Medicine

### Symbols
* `>` – Indicates a command to be entered in the terminal
* `[...]` – Placeholder for user-specified values

## Indications of Use
This application is intended for research use only. It facilitates advanced MRI reconstruction workflows using BART within a containerized environment, integrated into the Open Recon Application.

## Safety Considerations
### Definitions
* `Caution` – Indicates a potential hazard that could result in minor or moderate injury or equipment damage.

### List of Cautions
* Ensure Docker is installed and running before launching the container.
* Do not use this application for clinical diagnosis or patient care.

## Device Description
The application consists of a Docker container that encapsulates BART and its dependencies. It interfaces with the Open Recon Application to perform MRI image reconstruction tasks.

## Installation
Follow the instructions provided in Readme.md ...

## Instructions For Use
1. Update the `bart_wrap.py` file with the desired reconstruction using BART's python interface.
2. Update the `application_guide.md` and describe your created application.
3. Update the `appl_spec.json` file.
4. Run the `create_archive.sh` script and install the generated *.zip file at the scanner.

## Compatibility
* Compatible with Linux and Windows systems with Docker installed.
* Requires Open Recon Application version ...
* Supports BART version ... and above.

## Limitations
* Not intended for clinical use.
* No GPU support.

## Troubleshooting
| Issue                 | 	Solution                                                |
| --------              | -------                                                   |
|Container won't start  |	Ensure Docker is running and image is correctly pulled  |
|BART command not found	| Verify container image version and environment setup      |
|Data not processed	    | Check input format and file paths                         |

## Customer Support
For technical support, contact XXX at
* E-mail: this-is-an@example.com
* Phone: +49 123 456789

## Appendix
* BART Documentation: https://mrirecon.github.io/bart
* Docker Documentation: https://docs.docker.com

