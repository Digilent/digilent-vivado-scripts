# TODO: handle SDK projects.

set xpr_path [file normalize [lindex $argv 0]]
set repo_path [file normalize [lindex $argv 1]]
set vivado_version [lindex $argv 2]
set vivado_year [lindex [split $vivado_version "."] 0]

puts "INFO: Creating new project \"[file tail $xpr_path]\" in [file dirname $repo_path]/proj"

# Create project
set proj_name [file tail $xpr_path]
create_project $proj_name $repo_path/proj

# Capture board information for the project
source $repo_path/project_info.tcl

# Set project properties (using proc declared in project_info.tcl)
set obj [get_projects $proj_name]
set_digilent_project_properties $obj

# Uncomment the following 3 lines to greatly increase build speed while working with IP cores (and/or block diagrams)
set_property "corecontainer.enable" "0" $obj
set_property "ip_cache_permissions" "read write" $obj
set_property "ip_output_repo" "[file normalize "$repo_path/repo/cache"]" $obj

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
set_property "ip_repo_paths" "[file normalize $repo_path/repo]" $obj

# Refresh IP Repositories
update_ip_catalog -rebuild

# Add hardware description language sources
add_files -quiet -norecurse $repo_path/src/hdl

# Add IPs
# TODO: handle IP core-container files
add_files -quiet [glob -nocomplain $repo_path/src/ip/*/*.xci]

# Add constraints
add_files -quiet -norecurse -fileset constrs_1 $repo_path/src/constraints

# Recreate block design
if {[file exist [file normalize $repo_path/src/bd/system.tcl]]} {
    source $repo_path/src/bd/system.tcl

    # Generate the wrapper 
    set design_name [get_bd_designs]
    import_files -quiet -force -norecurse [make_wrapper -files [get_files $design_name.bd] -top -force]

    set obj [get_filesets sources_1]
    set_property "top" "${design_name}_wrapper" $obj
}

# Create 'synth_1' run (if not found)
if {[string equal [get_runs -quiet synth_1] ""]} {
    create_run -name synth_1 -part $board_part_name -flow {Vivado Synthesis $vivado_year} -strategy "Vivado Synthesis Defaults" -constrset constrs_1
} else {
    set_property strategy "Vivado Synthesis Defaults" [get_runs synth_1]
    set_property flow "Vivado Synthesis $vivado_year" [get_runs synth_1]
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
    create_run -name impl_1 -part $board_part_name -flow {Vivado Implementation $vivado_year} -strategy "Vivado Implementation Defaults" -constrset constrs_1 -parent_run synth_1
} else {
    set_property strategy "Vivado Implementation Defaults" [get_runs impl_1]
    set_property flow "Vivado Implementation $vivado_year" [get_runs impl_1]
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