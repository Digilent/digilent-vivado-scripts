foreach arg $argv {
	puts $arg
}

# Collect local sources, move them to ../src/<category>
# Collect sdk project & BSP & dummy hardware platform, and move them to ../sdk

# TODO: handle SDK projects.

set xpr_path [file normalize [lindex $argv 0]]
set repo_path [file normalize [lindex $argv 1]]
set proj_file [file tail $xpr_path]

puts "INFO: Checking project \"$proj_file\" into version control."
open_project $xpr_path

set required_dirs [list 			\
	$repo_path/proj					\
	$repo_path/src 					\
	$repo_path/src/bd 				\
	$repo_path/src/constraints 		\
	$repo_path/src/ip 				\
	$repo_path/src/hdl 				\
	$repo_path/src/others 			\
	$repo_path/repo 					\
	$repo_path/repo/local 			\
	$repo_path/repo/cache 			\
	$repo_path/sdk					\
]
set required_files [list 			\
	$repo_path/proj/.keep				\
	$repo_path/src/bd/.keep			\
	$repo_path/src/constraints/.keep	\
	$repo_path/src/ip/.keep			\
	$repo_path/src/hdl/.keep			\
	$repo_path/src/others/.keep		\
	$repo_path/repo/local/.keep		\
	$repo_path/repo/cache/.keep		\
	$repo_path/sdk/.keep				\
]
set files [list]

# Create any missing required directories and files
foreach d $required_dirs {
	if {[file exists $d] == 0} {
		file mkdir $d
	}
}
foreach f $required_files {
	if {[file exists $f] == 0} {
		close [open $f "w"]
	}
}

# Save source files, including block design tcl script
# WARNING: This script does not capture any non-xdc files for block-design projects
set bd_files [get_files -of_objects [get_filesets sources_1] -filter "NAME =~ *.bd"]
if {[llength $bd_files] > 1} {
	puts "ERROR: This script cannot handle projects containing more than one block design!"
} elseif {[llength $bd_files] == 1} {
	open_bd_design [lindex $bd_files 0]
	puts "INFO: Checking in system.tcl to version control."
	write_bd_tcl -force $repo_path/src/bd/system.tcl
	# TODO: Add support for "Add Module" IPI features (check in hdl files included in sources_1, but not any ip fileset)
} else {
	foreach source_file [get_files -of_objects [get_filesets sources_1]] {
		set origin [get_property name $source_file]
		if {[file extension $origin] == ".vhd"} {
			set subdir hdl
		} elseif {[file extension $origin] == ".v"} {
			set subdir hdl
		} elseif {[file extension $origin] != ".bd"} {
			set subdir other
		}
		puts "INFO: Checking in [file tail $origin] to version control."
		set target $repo_path/src/$subdir/[file tail $origin]
		if {$origin != $target} {
			file copy -force $origin $target
		}
	}
	# TODO: foreach file in /src/hdl & /src/others, if it wasn't just checked in, delete it
	
	foreach ip [get_ips] {
		set origin [get_property ip_file $ip]
		set ipname [get_property name $ip]
		set dir $repo_path/src/ip/$ipname
		if {[file exists $dir] == 0} {
			file mkdir $dir
		}
		set target $dir/[file tail $origin]
		puts "INFO: Checking in [file tail $origin] to version control."
		if {$origin != $target} {
			file copy -force $origin $target
		}
	}
	# TODO: foreach file in /src/ip, if it wasn't just checked in, delete it
}
foreach constraint_file [get_files -of_objects [get_filesets constrs_1]] {
	set origin [get_property name $constraint_file]
	set target $repo_path/src/constraints/[file tail $origin]
	puts "INFO: Checking in [file tail $origin] to version control."
	if {$origin != $target} {
		file copy -force $origin $target
	}
}
# TODO: foreach file in /src/constraints, if it wasn't just checked in, delete it

# Save project-specific settings into project_info.tcl
# TODO: will break if multiple projects are open
set proj_obj [get_projects [file rootname $proj_file]]
set board_part [current_board_part]
set part [get_property part $proj_obj]
set default_lib [get_property default_lib $proj_obj]
set simulator_language [get_property simulator_language $proj_obj]
set target_language [get_property target_language $proj_obj]
puts "INFO: Checking in project_info.tcl to version control."
set file_name $repo_path/proj/project_info.tcl
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