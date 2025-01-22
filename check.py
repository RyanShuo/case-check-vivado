import os
import subprocess
import shutil
import re
import sys

# Get the current directory where the script is located (assumed to be folder A)
base_dir = os.path.dirname(os.path.abspath(__file__))

# List to store subdirectories with non-standard cases
non_standard_cases = []

# List to store subdirectories with non-standard sdc folders
non_standard_sdc_cases = []

# List to store subdirectories with successful and failed synthesis cases
synth_success_cases = []
synth_fail_cases = []

# Define the FPGA part number (chip model) to be used in the Vivado project
fpga_part = "xcau15p-ffvb676-1-i"

# List of individual files to be deleted after processing
vivado_generated_items = [".Xil", "vivado.jou", "vivado.log"]

def find_netlist_and_top_module(sub_dir_path):
    """
    Find the .v netlist file in the netlist folder and extract the top module name.
    If no .v file is found or the netlist folder does not exist, return None.
    """
    netlist_dir = os.path.join(sub_dir_path, "netlist")
    
    if not os.path.exists(netlist_dir):
        return None  # No netlist folder found
    
    v_files = [f for f in os.listdir(netlist_dir) if f.endswith(".v")]
    if not v_files:
        return None  # No .v files found in netlist folder
    
    netlist_file_path = os.path.join(netlist_dir, v_files[0])
    
    # Extract the top module name from the .v file
    with open(netlist_file_path, "r") as file:
        for line in file:
            match = re.match(r'\s*module\s+(\w+)\s*\(', line)
            if match:
                top_module_name = match.group(1)
                return top_module_name  # Return the extracted top module name
    
    return None  # No module declaration found

def check_and_clean_sdc_folder(sub_dir_path):
    """
    Check and clean the sdc folder in the specified subdirectory.
    - If the sdc folder does not exist, print an error message and add to non-standard sdc cases.
    - If the sdc folder exists but does not contain timing.sdc, print an error message and add to non-standard sdc cases.
    - If the sdc folder contains files other than timing.sdc, delete those files.
    """
    sdc_dir = os.path.join(sub_dir_path, "sdc")
    
    if not os.path.exists(sdc_dir):
        print(f"Error: No sdc folder in {sub_dir_path}")
        non_standard_sdc_cases.append(sub_dir_path)
        return
    
    sdc_files = os.listdir(sdc_dir)
    
    if "timing.sdc" not in sdc_files:
        print(f"Error: Non-standard sdc folder in {sub_dir_path}")
        non_standard_sdc_cases.append(sub_dir_path)
        return
    
    # Delete all files in the sdc folder except timing.sdc
    for file in sdc_files:
        if file != "timing.sdc":
            file_path = os.path.join(sdc_dir, file)
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

def create_run_tcl(sub_dir_path, top_module_name):
    """
    Create a run.tcl file in the specified subdirectory with the given top module name.
    Also create a VIVADO folder to store the Vivado project files.
    """
    vivado_dir = os.path.join(sub_dir_path, "VIVADO")  # Define the VIVADO folder path
    rtl_dir = os.path.join(sub_dir_path, "rtl", "ori")  # Modify rtl_dir to point to rtl/ori
    
    run_tcl_content = f"""
# Define project and rtl directories
set project_dir "{vivado_dir}"
set rtl_dir "{rtl_dir}"

# Create the VIVADO project directory
file mkdir $project_dir

# Create a new Vivado project named 'test'
create_project test $project_dir -part {fpga_part}

# Add all source files in the rtl/ori directory
add_files -fileset sources_1 [glob -directory $rtl_dir *]

# Set the top module for the project
set_property top {top_module_name} [current_fileset]

# Update the compile order for the fileset
update_compile_order -fileset sources_1

# Get unreferenced files (before running synthesis)
set unref_files [get_files -of [get_filesets sources_1] -filter {{IS_AUTO_DISABLED}}]

# Run synthesis and implementation
catch {{ synth_design -top {top_module_name} }}
catch {{ place_design }}
catch {{ route_design }}

# Delete unreferenced files after synthesis and implementation
if {{[llength $unref_files] > 0}} {{
    puts "Deleting unreferenced files:"
    foreach file $unref_files {{
        if {{[file exists $file]}} {{
            file delete -force $file
            puts "  Deleted: $file"
        }}
    }}
}} else {{
    puts "No unreferenced files to delete."
}}

# Print completion message
puts "Synthesis and Implementation completed for project: {sub_dir_path}"
"""
    # Write the run.tcl file to the specified subdirectory
    run_tcl_path = os.path.join(sub_dir_path, "run.tcl")
    with open(run_tcl_path, "w") as file:
        file.write(run_tcl_content)
    print(f"Generated run.tcl in {sub_dir_path}")

def load_vivado_and_run_tcl(sub_dir_path):
    """
    Load Vivado environment and run the generated run.tcl script in batch mode.
    Determine success or failure based on whether 'ERROR' appears in Vivado output.
    """
    try:
        # Combine module load and vivado commands in a single shell execution
        vivado_command = "module load vivado/2024.2 && vivado -mode batch -source run.tcl"
        
        # Run Vivado and capture output
        result = subprocess.run(vivado_command, check=True, shell=True, cwd=sub_dir_path,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check Vivado output for errors
        output = result.stdout + result.stderr
        if "ERROR" in output:
            print(f"Error processing {sub_dir_path}: Synthesis or Implementation failed.")
            synth_fail_cases.append(sub_dir_path)  # Add to failure list
        else:
            print(f"Synthesis and Implementation succeeded for {sub_dir_path}")
            synth_success_cases.append(sub_dir_path)  # Add to success list

        # Collect deleted unreferenced files from Vivado output
        deleted_files = re.findall(r"Deleted: (.+)", output)
        if deleted_files:
            print(f"Deleted unreferenced files in {sub_dir_path}:")
            for file in deleted_files:
                print(f"  {file}")
        else:
            print(f"No unreferenced files to delete in {sub_dir_path}.")

    except subprocess.CalledProcessError as e:
        # If subprocess raises an error (non-zero exit code), treat it as a failure
        print(f"Error processing {sub_dir_path}: Command execution failed. Error: {e}")
        synth_fail_cases.append(sub_dir_path)  # Add to failure list

    except FileNotFoundError:
        # If Vivado or run.tcl is not found, treat it as a failure
        print(f"Error: Vivado or run.tcl not found in {sub_dir_path}")
        synth_fail_cases.append(sub_dir_path)  # Add to failure list

def delete_vivado_generated_items(sub_dir_path):
    """
    Delete Vivado-generated files and folders in the specified subdirectory.
    This includes the VIVADO folder and individual Vivado-generated files.
    """
    # Delete the VIVADO folder if it exists
    vivado_dir = os.path.join(sub_dir_path, "VIVADO")
    if os.path.exists(vivado_dir):
        shutil.rmtree(vivado_dir)  # Delete the entire VIVADO folder recursively
        print(f"Deleted VIVADO folder: {vivado_dir}")
    
    # Delete individual Vivado-generated files and folders
    for item in vivado_generated_items:
        item_path = os.path.join(sub_dir_path, item)
        if os.path.exists(item_path):
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Delete directory recursively
                print(f"Deleted folder: {item_path}")
            else:
                os.remove(item_path)  # Delete file
                print(f"Deleted file: {item_path}")

def process_subdirectories():
    """
    Iterate through all subdirectories in the base directory, process each one if it contains an rtl/ori folder.
    """
    for sub_dir in os.listdir(base_dir):
        sub_dir_path = os.path.join(base_dir, sub_dir)
        
        # Check if the path is a directory and contains the rtl/ori subdirectory
        if os.path.isdir(sub_dir_path) and os.path.exists(os.path.join(sub_dir_path, "rtl", "ori")):
            top_module = find_netlist_and_top_module(sub_dir_path)
            
            if top_module is None:
                # If no netlist found or no top module found, skip this subdirectory
                print("Skipping folder (no valid netlist found): {}".format(sub_dir_path))
                non_standard_cases.append(sub_dir_path)
                continue
            
            # Print a separator line and processing information
            print("\n" + "-" * 50)
            print(f"Processing folder: {sub_dir_path}")
            print(f"Top module found: {top_module}")
            
            # Create run.tcl with the extracted top module name
            create_run_tcl(sub_dir_path, top_module)
            
            # Run Vivado with the generated run.tcl script
            load_vivado_and_run_tcl(sub_dir_path)
            
            # Delete Vivado-generated files and folders
            delete_vivado_generated_items(sub_dir_path)
            
            # Check and clean the sdc folder after running Vivado
            check_and_clean_sdc_folder(sub_dir_path)
    
    # Print the list of non-standard cases
    if non_standard_cases:
        print("\n<List of Non-standard Case>:")
        for case in non_standard_cases:
            print(case)

    # Print the list of non-standard sdc cases
    if non_standard_sdc_cases:
        print("\n<List of Non-standard SDC Case>:")
        for case in non_standard_sdc_cases:
            print(case)

    # Print the list of successful synthesis cases
    if synth_success_cases:
        print("\n<List of Synthesis and Implementation Success Case>:")
        for case in synth_success_cases:
            print(case)

    # Print the list of failed synthesis cases
    if synth_fail_cases:
        print("\n<List of Synthesis and Implementation Failure Case>:")
        for case in synth_fail_cases:
            print(case)

if __name__ == "__main__":
    process_subdirectories()