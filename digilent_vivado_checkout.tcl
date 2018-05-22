# This script takes a Digilent Vivado Project's version controlled sources and creates a .xpr project containing them.
# It is assumed that this script is contained in a submodule directly below the root project directory.
# The created project will be placed in the ../proj directory relative to the location of this script.
# Call digilent-vivado-checkout.py instead to run this script outside of the Vivado GUI.

# TODO: handle SDK projects.

# Set up standard directory names
set orig_dir [pwd]
set proj_dir [file normalize ../[file dirname [info script]]]
set proj_name [file tail $proj_dir]
set src_dir $proj_dir/src
set repo_dir $proj_dir/repo
set sdk_dir $proj_dir/sdk
set board_dir $proj_dir/vivado-boards
set working_dir [file normalize $proj_dir/proj]

# Move into working directory
puts "INFO: Creating new project \"$proj_name\" in $working_dir"
cd $working_dir

# Associate board files submodule to project
# NOTE - this will override the setting of this param from an init script, this is desired behavior, as we do not want Vivado to see duplicate boards.
# FIXME - will this still work if a project is re-opened after the original script has been run?
set_param board.repoPaths [list $board_dir/new/board_files]
load_features core
enable_beta_device* 

# Create project
create_project $proj_name $working_dir

# Capture board information for the project
source ./project_info.tcl

# Set project properties (using proc declared in project_info.tcl)
set obj [get_projects $proj_name]
set_digilent_project_properties $obj

# Uncomment the following 3 lines to greatly increase build speed while working with IP cores (and/or block diagrams)
set_property "corecontainer.enable" "0" $obj
set_property "ip_cache_permissions" "read write" $obj
set_property "ip_output_repo" "[file normalize "$repo_dir/cache"]" $obj

# Create 'sources_1' fileset (if not found)
if {[string equal [get_filesets -quiet sources_1] ""]} {
    create_fileset -srcset sources_1
}

# Create 'constrs_1' fileset (if not found)
if {[string equal [get_filesets -quiet constrs_1] ""]} {
    create_fileset -constrset constrs_1
}

# Set IP repository paths
set obj [get_filesets sources_1]
set_property "ip_repo_paths" "[file normalize $repo_dir]" $obj

# Refresh IP Repositories
update_ip_catalog -rebuild

# TODO: Copy sources into project, instead of adding as remote. This will ensure that digilent-vivado-checkin must be called.
# Add hardware description language sources
add_files -quiet $src_dir/hdl

# Add IPs
# TODO: handle IP containers files
add_files -quiet [glob -nocomplain $src_dir/ip/*/*.xci]

# Add constraints
add_files -fileset constrs_1 -quiet $src_dir/constraints

# Recreate block design
if {[file exist [file normalize $src_dir/bd/system.tcl]]} {
    source $src_dir/bd/system.tcl

    # Generate the wrapper 
    set design_name [get_bd_designs]
    add_files -norecurse [make_wrapper -files [get_files $design_name.bd] -top -force]

    set obj [get_filesets sources_1]
    set_property "top" "${design_name}_wrapper" $obj
}

# Create 'synth_1' run (if not found)
if {[string equal [get_runs -quiet synth_1] ""]} {
    create_run -name synth_1 -part $board_part_name -flow {Vivado Synthesis 2017} -strategy "Vivado Synthesis Defaults" -constrset constrs_1
} else {
    set_property strategy "Vivado Synthesis Defaults" [get_runs synth_1]
    set_property flow "Vivado Synthesis 2017" [get_runs synth_1]
}
set obj [get_runs synth_1]
set_property "part" $board_part_name $obj
set_property "steps.synth_design.args.flatten_hierarchy" "none" $obj
set_property "steps.synth_design.args.directive" "RuntimeOptimized" $obj
set_property "steps.synth_design.args.fsm_extraction" "off" $obj

# Set the current synth run
current_run -synthesis [get_runs synth_1]

# Create 'impl_1' run (if not found)
if {[string equal [get_runs -quiet impl_1] ""]} {
    create_run -name impl_1 -part $board_part_name -flow {Vivado Implementation 2017} -strategy "Vivado Implementation Defaults" -constrset constrs_1 -parent_run synth_1
} else {
    set_property strategy "Vivado Implementation Defaults" [get_runs impl_1]
    set_property flow "Vivado Implementation 2017" [get_runs impl_1]
}
set obj [get_runs impl_1]
set_property "part" $board_part_name $obj
set_property "steps.opt_design.args.directive" "RuntimeOptimized" $obj
set_property "steps.place_design.args.directive" "RuntimeOptimized" $obj
set_property "steps.route_design.args.directive" "RuntimeOptimized" $obj

# Set the current impl run
current_run -implementation [get_runs impl_1]

# Return to original calling location
cd $orig_dir
puts "INFO: Project created: $proj_name"