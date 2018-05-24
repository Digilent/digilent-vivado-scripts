# Collect local sources, move them to ../src/<category>
# Collect sdk project & BSP & dummy hardware platform, and move them to ../sdk

# TODO: handle SDK projects.

set orig_dir [pwd]
set proj_dir [file normalize ../[file dirname [info script]]]
set proj_name [file tail $proj_dir]

# Check if project working directory exists
if {[file exists $proj_dir/proj] == 0} {
	file mkdir $proj_dir/proj
}
if {[file exists $proj_dir/proj/.keep] == 0} {
	close [open $proj_dir/proj/.keep "w"]
}

# Move into working directory and open the XPR (or fail and log an error)
puts "INFO: Checking project \"$proj_name.xpr\" into version control."
cd $proj_dir/proj
open_project $proj_name.xpr

# Check repo to see if it matches expected format. Create missing directories and .keep files
# INFO: This block makes the creation of a template repository unnecessary.
if {[file exists $proj_dir/src] == 0} {
	file mkdir $proj_dir/src
}
if {[file exists $proj_dir/src/bd] == 0} {
	file mkdir $proj_dir/src/bd
}
if {[file exists $proj_dir/src/bd/.keep] == 0} {
	close [open $proj_dir/src/bd/.keep "w"]
}
if {[file exists $proj_dir/src/constraints] == 0} {
	file mkdir $proj_dir/src/constraints
}
if {[file exists $proj_dir/src/constraints/.keep] == 0} {
	close [open $proj_dir/src/constraints/.keep "w"]
}
if {[file exists $proj_dir/src/hdl] == 0} {
	file mkdir $proj_dir/src/hdl
}
if {[file exists $proj_dir/src/hdl/.keep] == 0} {
	close [open $proj_dir/src/hdl/.keep "w"]
}
if {[file exists $proj_dir/src/ip] == 0} {
	file mkdir $proj_dir/src/ip
}
if {[file exists $proj_dir/src/ip/.keep] == 0} {
	close [open $proj_dir/src/ip/.keep "w"]
}
if {[file exists $proj_dir/src/other] == 0} {
	file mkdir $proj_dir/src/other
}
if {[file exists $proj_dir/src/other/.keep] == 0} {
	close [open $proj_dir/src/other/.keep "w"]
}

if {[file exists $proj_dir/repo] == 0} {
	file mkdir $proj_dir/repo
}
if {[file exists $proj_dir/repo/local] == 0} {
	file mkdir $proj_dir/repo/local
}
if {[file exists $proj_dir/repo/local/.keep] == 0} {
	close [open $proj_dir/repo/local/.keep "w"]
}
if {[file exists $proj_dir/repo/cache] == 0} {
	file mkdir $proj_dir/repo/cache
}
if {[file exists $proj_dir/repo/cache/.keep] == 0} {
	close [open $proj_dir/repo/cache/.keep "w"]
}

if {[file exists $proj_dir/sdk] == 0} {
	file mkdir $proj_dir/sdk
}
if {[file exists $proj_dir/sdk/.keep] == 0} {
	close [open $proj_dir/sdk/.keep "w"]
}

if {[file exists $proj_dir/sdk] == 0} {
	file mkdir $proj_dir/sdk
}
if {[file exists $proj_dir/sdk/.keep] == 0} {
	close [open $proj_dir/sdk/.keep "w"]
}

# Save source files, including block design tcl script
# WARNING: This script does not capture any non-xdc files for block-design projects
# TODO: Add support for "Add Module" IPI feature
set bd_files [get_files -of_objects [get_filesets sources_1] -filter "NAME =~ *.bd"]
if {[llength $bd_files] == 1} {
	open_bd_design [lindex $bd_files 0]
	set tcl_filename $proj_dir/src/bd/system.tcl
	puts "INFO: Checking in system.tcl to version control."
	write_bd_tcl -force $tcl_filename
} elseif {[llength $bd_files] > 1} {
	# TODO
	puts "ERROR: This script cannot handle projects containing more than one block design!"
} else {
	foreach source_file [get_files -of_objects [get_filesets sources_1]] {
		set origin [get_property name $source_file]
		if {[file extension $origin] == ".vhd"} {
			set target $proj_dir/src/hdl/[file tail $origin]
		} elseif {[file extension $origin] == ".v"} {
			set target $proj_dir/src/hdl/[file tail $origin]
		} elseif {[file extension $origin] != ".bd"} {
			set target $proj_dir/src/other/[file tail $origin]
		}
		puts "INFO: Checking in [file tail $target] to version control."
		if {$origin != $target} {
			file copy -force $origin $target
		}
	}
	foreach ip [get_ips] {
		set origin [get_property ip_file $ip]
		set ipname [get_property name $ip]
		set dir $proj_dir/src/ip/$ipname
		if {[file exists $dir] == 0} {
			file mkdir $dir
		}
		set target $dir/[file tail $origin]
		puts "INFO: Checking in [file tail $target] to version control."
		if {$origin != $target} {
			file copy -force $origin $target
		}
	}
}
foreach constraint_file [get_files -of_objects [get_filesets constrs_1]] {
	set origin [get_property name $constraint_file]
	set target $proj_dir/src/constraints/[file tail $origin]
	puts "INFO: Checking in [file tail $target] to version control."
	if {$origin != $target} {
		file copy -force $origin $target
	}
}

# Save project-specific settings into project_info.tcl
set board_part [current_board_part]
set part [get_property part [get_projects $proj_name]]
set default_lib [get_property default_lib [get_projects $proj_name]]
set simulator_language [get_property simulator_language [get_projects $proj_name]]
set target_language [get_property target_language [get_projects $proj_name]]
puts "INFO: Checking in project_info.tcl to version control."
set file_name $proj_dir/proj/project_info.tcl
set file_obj [open $file_name "w"]
puts $file_obj "# This is an automatically generated file used by digilent_vivado_checkout.tcl to set project options"
puts $file_obj "proc set_digilent_project_properties {project_obj} {"
puts $file_obj "	set_property \"board_part\" \"$board_part\" \$project_obj"
puts $file_obj "	set_property \"part\" \"$part\" \$project_obj"
puts $file_obj "	set_property \"default_lib\" \"$default_lib\" \$project_obj"
puts $file_obj "	set_property \"simulator_language\" \"$simulator_language\" \$project_obj"
puts $file_obj "	set_property \"target_language\" \"$target_language\" \$project_obj"
puts $file_obj "}"
close $file_obj

# Return to directory that the script was called from
cd $orig_dir
