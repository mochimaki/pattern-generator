# Pattern Generator Environment Setup Guide

## 1. Overview
This document outlines the environment setup procedure for running the Pattern Generator application.

## 2. Prerequisites
- Anaconda3 must be installed
- Windows 10 or later environment

## 3. Environment Setup Procedure

### 3.1. Creating Conda Environment
```bash
# Create a new environment (using Python 3.11)
conda create -n pattern_generator python=3.11
conda activate pattern_generator
```

### 3.2. Installing Flet Packages
```bash
# Install Flet-related packages (specify version 0.26.0)
pip install flet-cli==0.26.0  # flet 0.26.0 will also be installed
pip install flet-desktop==0.26.0
pip install flet-web==0.26.0
```

### 3.3. Installing Required Packages
```bash
# Install required packages using conda-forge channel
conda install pandas matplotlib numpy libm2k -c conda-forge
```

This command will install the following packages and their dependencies:
- pandas
- matplotlib
- numpy
- libm2k
- Other dependency packages (qt, mkl, etc.)

## 4. Directory Structure Preparation
The application requires the following directory structure:

```
project_directory/
├── pattern_generator/        # Application root (app root)
│   ├── pattern_generator.py  # Main application
│   ├── chart_func.py         # Chart-related functions
│   ├── edit_operations.py    # Edit operation functions
│   ├── export_csv.py         # CSV export functions
│   ├── file_operations.py    # File operation functions
│   ├── m2k_digital.py        # ADALM2000 device control functions
│   └── view_operations.py    # View operation functions
├── pkl_files/                # Part of data root
├── csv_files/                # Part of data root
└── app_info.json             # Application configuration file
```

### 4.1. Directory Structure Explanation
This project adopts a design that clearly separates application and data:

- **Application Root (app root)**
  - The `pattern_generator/` directory serves as the application root
  - Contains all Python programs required for application execution
  - Directory name matches the main program (`pattern_generator.py`)

- **Data Root**
  - `pkl_files/` and `csv_files/` directories serve as the data root
  - Represents the highest level hierarchy accessible to the application
  - Programs cannot access levels above the data root

This design offers the following advantages:
- Enables flexible control of mounting methods for applications and data in container environments
- Allows creation of relationships between data root and application root using symbolic links when running as a desktop application
- Facilitates building systems that integrate multiple applications by developing multiple projects with the same structure

Create the required directories:
```bash
mkdir pattern_generator pkl_files csv_files
```

### 4.2. Creating app_info.json
`app_info.json` stores connection settings for the ADALM2000 device. Create it with the following content:

```json
{
    "devices": {
        "m2k": {
            "target": ["192.168.2.1"]
        }
    }
}
```

Place this file directly under the project directory. Change the IP address in `target` to match the actual IP address of your ADALM2000 device.

## 5. Verification
```bash
cd pattern_generator
python pattern_generator.py
```

Upon successful startup, the following message will be displayed:
```bash
Error loading settings: [Errno 2] No such file or directory: '../app_info.json'
Channel list is empty. Returning empty chart.
```
※This is a normal message for the first startup.

## 6. Notes
- Use Flet version 0.26.0 (for `Colors` attribute compatibility)
- Install packages using the conda-forge channel
- `pkl_files` and `csv_files` directories are not created automatically and must be created manually
- `app_info.json` should not be included in the repository and should be created in the local environment
- All Python files must be placed in the `pattern_generator` directory
- The application cannot access levels above the data root

## 7. Troubleshooting
- If a module not found error occurs, install the corresponding package individually
- If path-related errors occur, verify that the required directory structure is correctly created
- If permission errors occur during file operations, check directory permissions
- If unable to connect to ADALM2000 device, verify the IP address in `app_info.json`
- Verify that all required Python files exist in the `pattern_generator` directory
- If data access errors occur, check the data root directory structure

## 8. Reference Information
- Flet Official Documentation: https://flet.dev/
- Conda-forge: https://conda-forge.org/
- Libm2k Documentation: https://analogdevicesinc.github.io/libm2k/

## 9. Update History
- 2024-03-27: Initial version created
- 2024-03-27: Modified Flet package installation procedure
- 2024-05-03: Added app_info.json configuration content
- 2024-05-04: Corrected directory structure
- 2024-05-04: Added explanation of application root and data root concepts and purposes