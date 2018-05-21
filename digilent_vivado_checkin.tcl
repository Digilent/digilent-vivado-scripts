# Collect local sources, move them to ../src/<category>
# Collect sdk project & BSP & dummy hardware platform, and move them to ../sdk

# TODO: handle SDK projects.

set orig_dir [pwd]
set proj_dir [file normalize ../[file dirname [info script]]]
set proj_name [file tail $proj_dir]
set src_dir $proj_dir/src
set repo_dir $proj_dir/repo
set sdk_dir $proj_dir/sdk
set board_dir $proj_dir/vivado-boards
set working_dir [file normalize $proj_dir/proj]

# Move into working directory
puts "INFO: Checking project \"$proj_name.xpr\" into version control"
cd $working_dir

open_project $proj_name.xpr

# TODO: Generate list of other sources. Place each at <proj_dir>/src/other/<name>.<extension>
# IF block design project
	# Generate system.tcl script. Place at <proj_dir>/src/bd/system.tcl
	# ???
	# Profit
# ELSE
	# Generate list of all xci files. Place each at <proj_dir>/src/ip/<name>/<name>.xci
	# Generate list of hdl sources (not including block design wrapper). Place each at <proj_dir>/src/hdl/<name>.[v|vhd]

foreach source_file [get_files -of_objects [get_filesets sources_1]] {
	set origin [get_property name $source_file]
	if {[file extension $origin] == ".vhd"} {
		set target $proj_dir/src/hdl/[file tail $origin]
	} elseif {[file extension $origin] == ".v"} {
		set target $proj_dir/src/hdl/[file tail $origin]
	} else {
		set target $proj_dir/src/other/[file tail $origin]
	}
	puts "INFO: Checking in [file tail $target] to version control."
	file copy -force $origin $target
}
foreach constraint_file [get_files -of_objects [get_filesets constrs_1]] {
	set origin [get_property name $constraint_file]
	set target $proj_dir/src/constraints/[file tail $origin]
	puts "INFO: Checking in [file tail $target] to version control."
	file copy -force $origin $target
}
foreach ip [get_ips] {
	set origin [get_property ip_file $ip]
	set ipname [get_property name $ip]
	set dir $proj_dir/src/ip/$ipname
	if {[file exists $dir] == 0} {
		file mkdir $dir
	}
	set target $dir/[file tail $origin]
	puts "INFO: Checking in [file tail $target] to version control"
	file copy -force $origin $target
}

cd $orig_dir