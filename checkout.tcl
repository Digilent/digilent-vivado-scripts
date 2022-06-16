# Note: argument order does not matter when setting argv; all arguments are optional
# Usage (No Defaults):
#   set argv "-r <repo_path> -x <xpr_path> -v <vivado_version> -b -no-block"
#   source digilent_vivado_checkout.tcl
# Usage (All Defaults):
#   set argv ""
#   source digilent_vivado_checkout.tcl
# TODO: add debug flag for argument checking

# Handle repo_path argument
set idx [lsearch ${argv} "-r"]
if {${idx} != -1} {
    set repo_path [glob -nocomplain [file normalize [lindex ${argv} [expr {${idx}+1}]]]]
} else {
    # Default
    set repo_path [file normalize [file dirname [info script]]/..]
}

# Handle xpr_path argument
set idx [lsearch ${argv} "-x"]
if {${idx} != -1} {
    set xpr_path [file normalize [lindex ${argv} [expr {${idx}+1}]]]
} else {
    # Default
    set xpr_path [file join ${repo_path} proj [file tail $repo_path]].xpr]
}

# Handle vivado_version argument
set idx [lsearch ${argv} "-v"]
if {${idx} != -1} {
    set vivado_version [lindex ${argv} [expr {${idx}+1}]]
} else {
    # Default
    set vivado_version [version -short]
}

# Handle build flag
set idx [lsearch ${argv} "-b"]
if {${idx} != -1} {
    set build_when_checked_out 1
} else {
    # Default
    set build_when_checked_out 0
}

# Handle no block flag
set idx [lsearch ${argv} "-no-block"]
if {${idx} != -1} {
    set wait_on_build 0
} else {
    # Default
    set wait_on_build 1
}

# Other variables
set vivado_year [lindex [split $vivado_version "."] 0]
set proj_name [file rootname [file tail $xpr_path]]

puts "INFO: Creating new project \"$proj_name\" in [file dirname $xpr_path]"

# Create project
create_project $proj_name [file dirname $xpr_path]

source $repo_path/project_info.tcl

# Capture board information for the project
puts "INFO: Capturing board information from $repo_path/project_info.tcl"
set_project_properties_post_create_project $proj_name
set obj [get_projects $proj_name]
set part_name [get_property "part" $obj]

# Uncomment the following 3 lines to greatly increase build speed while working with IP cores (and/or block diagrams)
puts "INFO: Configuring project IP handling properties"
set_property "corecontainer.enable" "0" $obj
set_property "ip_cache_permissions" "read write" $obj
set_property "ip_output_repo" "[file normalize "$repo_path/proj/cache"]" $obj

# Create 'sources_1' fileset (if not found)
if {[string equal [get_filesets -quiet sources_1] ""]} {
    puts "INFO: Creating sources_1 fileset"
    create_fileset -srcset sources_1
}

# Create 'constrs_1' fileset (if not found)
if {[string equal [get_filesets -quiet constrs_1] ""]} {
    puts "INFO: Creating constrs_1 fileset"
    create_fileset -constrset constrs_1
}

# Capture project-specific IP settings
puts "INFO: capturing IP-related settings from $repo_path/project_info.tcl"
set_project_properties_pre_add_repo $proj_name

# Set IP repository paths
puts "INFO: Setting IP repository paths"
set obj [get_filesets sources_1]
set_property "ip_repo_paths" "[file normalize $repo_path/repo]" $obj

# Refresh IP Repositories
puts "INFO: Refreshing IP repositories"
update_ip_catalog -rebuild

# Add hardware description language sources
puts "INFO: Adding HDL sources"
add_files -quiet -norecurse $repo_path/src/hdl

# Add IPs
# TODO: handle IP core-container files
puts "INFO: Adding XCI IP sources"
add_files -quiet [glob -nocomplain $repo_path/src/ip/*/*.xci]

# Add constraints
puts "INFO: Adding constraints"
add_files -quiet -norecurse -fileset constrs_1 $repo_path/src/constraints

# Recreate block design
# TODO: handle multiple block designs
set ipi_tcl_files [glob -nocomplain "$repo_path/src/bd/*.tcl"]
set ipi_bd_files [glob -nocomplain "$repo_path/src/bd/*/*.bd"]
if {[llength $ipi_tcl_files] > 1} {
    # TODO: quit and log the error
    puts "ERROR: This script cannot handle projects containing more than one block design! More than one tcl script foudn in src/bd"
} elseif {[llength $ipi_tcl_files] == 1} {
    # Use TCL script to rebuild block design
    puts "INFO: Rebuilding block design from script"
    # Create local source directory for bd
    if {[file exist "[file rootname $xpr_path].srcs"] == 0} {
        file mkdir "[file rootname $xpr_path].srcs"
    }
    if {[file exist "[file rootname $xpr_path].srcs/sources_1"] == 0} {
        file mkdir "[file rootname $xpr_path].srcs/sources_1"
    }
    if {[file exist "[file rootname $xpr_path].srcs/sources_1/bd"] == 0} {
        file mkdir "[file rootname $xpr_path].srcs/sources_1/bd"
    }
    # Force Non-Remote BD Flow
    set origin_dir [pwd]
    cd "[file rootname $xpr_path].srcs/sources_1"
    set run_remote_bd_flow 0
    if {[set result [catch { source [lindex $ipi_tcl_files 0] } resulttext]]} {
        # remember global error state
        set einfo $::errorInfo
        set ecode $::errorCode
        catch {cd $origin_dir}
        return -code $result -errorcode $ecode -errorinfo $einfo $resulttext
    }
    cd $origin_dir
} elseif {[llength $ipi_bd_files] > 1} {
    # TODO: quit and log the error
    puts "ERROR: This script cannot handle projects containing more than one block design! More than one bd file foudn in src/bd"
} elseif {[llength $ipi_bd_files] == 1} {
    # Add block design from .bd file and sources
    puts "INFO: Rebuilding block design from BD fileset"
    add_files -norecurse -quiet -fileset sources_1 [glob -nocomplain $repo_path/src/bd/*/*.bd]
    open_bd_design [glob -nocomplain $repo_path/src/bd/*/*.bd]
    set design_name [get_bd_designs]
    set file "$repo_path/src/bd/$design_name/$design_name.bd"
    set file [file normalize $file]
    set file_obj [get_files -of_objects [get_filesets sources_1] [list "*$file"]]
    if { ![get_property "is_locked" $file_obj] } {
        set_property "synth_checkpoint_mode" "Hierarchical" $file_obj
    }
}

# Make sure IPs are upgraded to the most recent version
foreach ip [get_ips -filter "IS_LOCKED==1"] {
    upgrade_ip -vlnv [get_property UPGRADE_VERSIONS $ip] $ip
    export_ip_user_files -of_objects $ip -no_script -sync -force -quiet
}

# Generate the wrapper for the root design
catch {
	# catch block prevents projects without a block design from erroring at this step
	set bd_name [get_bd_designs -of_objects [get_bd_cells /]]
	set bd_file [get_files $bd_name.bd]
	set wrapper_file [make_wrapper -files $bd_file -top -force]
	import_files -quiet -force -norecurse $wrapper_file

	set obj [get_filesets sources_1]
	set_property "top" "${bd_name}_wrapper" $obj
}

# Create 'synth_1' run (if not found)
if {[string equal [get_runs -quiet synth_1] ""]} {
    puts "INFO: Creating synth_1 run"
    create_run -name synth_1 -part $part_name -flow {Vivado Synthesis $vivado_year} -strategy "Vivado Synthesis Defaults" -constrset constrs_1
} else {
    set_property strategy "Vivado Synthesis Defaults" [get_runs synth_1]
    set_property flow "Vivado Synthesis $vivado_year" [get_runs synth_1]
}
puts "INFO: Configuring synth_1 run"
set obj [get_runs synth_1]
set_property "part" $part_name $obj

# Set the current synth run
puts "INFO: Setting current synthesis run"
current_run -synthesis [get_runs synth_1]

# Create 'impl_1' run (if not found)
if {[string equal [get_runs -quiet impl_1] ""]} {
    puts "INFO: Creating impl_1 run"
    create_run -name impl_1 -part $part_name -flow {Vivado Implementation $vivado_year} -strategy "Vivado Implementation Defaults" -constrset constrs_1 -parent_run synth_1
} else {
    set_property strategy "Vivado Implementation Defaults" [get_runs impl_1]
    set_property flow "Vivado Implementation $vivado_year" [get_runs impl_1]
}
puts "INFO: Configuring impl_1 run"
set obj [get_runs impl_1]
set_property "part" $part_name $obj

# Set the current impl run
puts "INFO: Setting current implementation run"
current_run -implementation [get_runs impl_1]

# Capture project-specific IP settings
puts "INFO: capturing run settings from $repo_path/project_info.tcl"
set_project_properties_post_create_runs $proj_name

# Get the post_build script path
set post_build_script_path [file join ${repo_path} post_build.tcl]
set post_build_script [glob -nocomplain ${post_build_script_path}]

# Launch a build if -b was specified
if {${build_when_checked_out}} {
    launch_runs -to_step write_bitstream impl_1
    # Wait until the project has been built if -no-block wasn't specified
    if {${wait_on_build}} {
        wait_on_run impl_1
        puts "INFO: Build complete"

        # If it exists, run the post_build script. This can be used to export 
        if {${post_build_script} ne ""} {
            source ${post_build_script}
        } else {
            puts "INFO: No post_build script found"
        }
    } else {
        if {${post_build_script} ne ""} {
            puts "WARNING: Build launched but ${post_build_script} has not been run"
            puts "         After the bitstream has been generated, run the command 'source ${post_build_script}'"
        } else {
            puts "INFO: No post_build script found"
        }
    }
}

puts "INFO: Project created: [file tail $proj_name]"
puts "INFO: Exiting digilent_vivado_checkout"