![image](https://github.com/user-attachments/assets/a488bb21-8571-48c1-bcb3-0b87ba4ee876)# check.py Script - README

## Developer
Developed by: **Shuo Ru**  
Email: **rushuo@outlook.com**  
Date: **2025/1/17**

## Overview
The `check.py` script automates the following tasks for FPGA design directories:

1. **Netlist and Top Module Extraction**: Extracts the top module from the netlist files.
2. **SDC Folder Validation**: Validates the `sdc` folder and deletes non-standard files.
3. **Vivado Project Creation**: Creates a Vivado project and generates `run.tcl` for synthesis and implementation.
4. **Unreferenced File Deletion**: Deletes unreferenced files from the Vivado project.
5. **Synthesis and Implementation**: Runs Vivado synthesis and implementation.
6. **Logging**: Logs the details for each processed case.

## Environment
- **Python 3.x**  
- **Conda**: `/tools/misc/conda`  
- **Vivado 2024.2** installed and accessible.
- **Linux**

## Requirements
- Case structure:  
  - `netlist/` containing `.v` netlist files.  
  - `rtl/ori/` containing RTL Verilog files.  
  - Optional `sdc/` folder for timing constraints.

## How to Run
1. Ensure Vivado is installed and accessible.  
2. Place `check.py` in the base directory containing subdirectories (`Case1`, `Case2`, etc.).  
3. Run the script.

## Project Directory Structure

The following outlines the structure of the project directories:

```plaintext
/base_dir/
├── check.py  # This script
├── case1/
│   ├── rtl/
│   │   └── ori/
│   ├── netlist/
│   │   └── xxx.v
│   └── sdc/
│       └── timing.sdc
└── case2/
    ├── rtl/
    │   └── ori/
    ├── netlist/
    │   └── xxx.v
    └── sdc/
        └── timing.sdc
```
##  Note：

- /base_dir/: The root directory of the project.
- check.py: The main script for automating checks, synthesis, and implementation for FPGA designs.
- case1/ and case2/: Directories for each design case.
- rtl/ori/: Contains the original RTL Verilog files.
- netlist/: Contains the netlist files.
- sdc/: Contains timing constraint files.
