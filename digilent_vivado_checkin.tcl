# Note: argument order does not matter when setting argv; all arguments are optional
# Usage (No Defaults):
#   set argv "-r <repo_path> -x <xpr_path> -v <vivado_version>"
#   source digilent_vivado_checkin.tcl
# Usage (All Defaults):
#   set argv ""
#   source digilent_vivado_checkin.tcl
# TODO: add debug flag for argument checking

set script_dir [file normalize [file dirname [info script]]]

foreach arg $argv {
    puts $arg
}

# Collect local sources, move them to ../src/<category>

# Handle repo_path argument
set idx [lsearch ${argv} "-r"]
if {${idx} != -1} {
    set repo_path [glob -nocomplain [file normalize [lindex ${argv} [expr {${idx}+1}]]]]
} else {
    # Default
    set repo_path [file normalize [file join [file dirname [info script]] ..]]
}

# Handle xpr_path argument
set idx [lsearch ${argv} "-x"]
if {${idx} != -1} {
    set xpr_path [glob -nocomplain [file normalize [lindex ${argv} [expr {${idx}+1}]]]]
} else {
    # Default
    set xpr_path [glob -nocomplain "${repo_path}/proj/*.xpr"]
}
if {[llength ${xpr_path}] != 1} {
    puts "ERROR: XPR not found"
} else {
    set xpr_path [lindex ${xpr_path} 0]
}

# Handle vivado_version argument
set idx [lsearch ${argv} "-v"]
if {${idx} != -1} {
    set vivado_version [lindex ${argv}]
} else {
    set vivado_version [version -short]
}

set vivado_version [lindex $argv 2]; # unused

# Other variables
set force_overwrite_info_script 0; # included for possible argument support in future
set proj_file [file tail $xpr_path]
set proj_dir [file dirname $xpr_path]
set proj_name [file rootname [file tail $proj_file]]

puts "INFO: Checking project \"$proj_file\" into version control."
set already_opened [get_projects -filter "DIRECTORY==$proj_dir && NAME==$proj_name"]
if {[llength $already_opened] == 0} {
    open_project $xpr_path
} else {
    current_project [lindex $already_opened 0]
}



set required_dirs [list                 \
    $repo_path/proj                     \
    $repo_path/hw_handoff               \
    $repo_path/src                      \
    $repo_path/src/bd                   \
    $repo_path/src/constraints          \
    $repo_path/src/ip                   \
    $repo_path/src/hdl                  \
    $repo_path/src/other                \
    $repo_path/repo                     \
    $repo_path/repo/local               \
]
set required_files [list                \
    $repo_path/proj/.keep               \
    $repo_path/hw_handoff/.keep         \
    $repo_path/src/bd/.keep             \
    $repo_path/src/constraints/.keep    \
    $repo_path/src/ip/.keep             \
    $repo_path/src/hdl/.keep            \
    $repo_path/src/other/.keep          \
    $repo_path/repo/local/.keep         \
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
set bd_files [get_files -of_objects [get_filesets sources_1] -filter "NAME=~*.bd"]
if {[llength $bd_files] > 1} {
    puts "ERROR: This script cannot handle projects containing more than one block design!"
} elseif {[llength $bd_files] == 1} {
    set bd_file [lindex $bd_files 0]
    open_bd_design $bd_file
    set bd_name [file tail [file rootname [get_property NAME $bd_file]]]
    set script_name "$repo_path/src/bd/${bd_name}.tcl"
    puts "INFO: Checking in ${script_name} to version control."
    write_bd_tcl -force -make_local $script_name
	
	# Check in source files used in RTL module references (work in progress)
	set root_design [get_property NAME [get_bd_cells /]]
	set fileset [get_filesets sources_1]
	# filter expression:
	#     is_generated is true when a file is part of an IP.
	#     file_type specification filters out unnecessary files
	#     name filters out the block design wrapper file
	set module_ref_sources [get_files -of_objects $fileset -filter "!IS_GENERATED && FILE_TYPE!={Block Designs} && FILE_TYPE!={Configuration Files} && NAME!~*/${root_design}_wrapper.*"]

	foreach module_ref_source $module_ref_sources {
		set origin [get_property name $module_ref_source]
        
		set subdir hdl
		if {[lsearch ".v .vhd .sv" [file extension $origin]] != -1} {
            puts "INFO: Checking in [file tail $origin] to version control."
            set target $repo_path/src/$subdir/[file tail $origin]
            if {[file exists $target] == 0} {
                file copy -force $origin $target
            }
		}
	}
} else {
    foreach source_file [get_files -of_objects [get_filesets sources_1]] {
        set origin [get_property name $source_file]
        set skip 0
        if {[file extension $origin] == ".vhd"} {
            set subdir hdl
        } elseif {[file extension $origin] == ".v"} {
            set subdir hdl
        } elseif {[file extension $origin] == ".sv"} {
            set subdir hdl
        } elseif {[file extension $origin] != ".bd" && [file extension $origin] != ".xci"} {
            set subdir other
        } else {
            set skip 1
        }
        
        foreach ip [get_ips] {
            set ip_dir [get_property IP_DIR $ip]
            set source_length [string length $source_file]
            set dir_length [string length $ip_dir]
            if {$source_length >= $dir_length && [string range $source_file 0 $dir_length-1] == $ip_dir} {
                set skip 1
            }
        }
        
        if {$skip == 0} {
            puts "INFO: Checking in [file tail $origin] to version control."
            set target $repo_path/src/$subdir/[file tail $origin]
            if {[file exists $target] == 0} { # TODO: this may not be safe; remind users to make sure to delete any unused files from version control
                file copy -force $origin $target
            }
        }
    }
    foreach ip [get_ips] {
        set origin [get_property ip_file $ip]
        set ipname [get_property name $ip]
        set dir "$repo_path/src/ip/$ipname"
        if {[file exists $dir] == 0} {
            file mkdir $dir
        }
        set target $dir/[file tail $origin]
        puts "INFO: Checking in [file tail $origin] to version control."
        if {[file exists $target] == 0} {
            # TODO: this may not be safe; remind users to make sure to delete any unused files from version control
            file copy -force $origin $target
        }
    }
    # TODO: foreach file in /src/ip, if it wasn't just checked in, delete it
}
foreach constraint_file [get_files -of_objects [get_filesets constrs_1]] {
    set origin [get_property name $constraint_file]
    set target $repo_path/src/constraints/[file tail $origin]
    puts "INFO: Checking in [file tail $origin] to version control."
        if {[file exists $target] == 0} { # TODO: this may not be safe; remind users to make sure to delete any unused files from version control
        file copy -force $origin $target
    }
}
# TODO: foreach file in /src/constraints, if it wasn't just checked in, delete it

# Save project-specific settings into project_info.tcl
# TODO: will break if multiple projects are open
# project_info.tcl will only be created if it doesn't exist - if it has been manually deleted by the user, or if this is the first time this repo is checked in
if {[file exists $repo_path/project_info.tcl] == 0 || $force_overwrite_info_script != 0} {
    set proj_obj [get_projects [file rootname $proj_file]]
    
    set board_part [current_board_part -quiet]
    set part [get_property part $proj_obj]
    set default_lib [get_property default_lib $proj_obj]
    set simulator_language [get_property simulator_language $proj_obj]
    set target_language [get_property target_language $proj_obj]
    
    puts "INFO: Checking in project_info.tcl to version control."
    
    set var_map [list <part> $part                             \
                      <default_lib> $default_lib               \
                      <simulator_language> $simulator_language \
                      <target_language> $target_language       \
    ]
    
    if {$board_part ne ""} {
        lappend var_map <board_part> $board_part
    }
    
    set file_name $repo_path/project_info.tcl
    set dfid [open $file_name "w"]
    set sfid [open $script_dir/templates/project_info.tcl "r"]
    
    while { [gets $sfid line] >= 0 } {
        puts $dfid [string map $var_map $line]
    }
    
    close $dfid
    close $sfid
}

# if .gitignore does not exist, create it
set master_gitignore [file join $repo_path .gitignore]
if {[file exists $master_gitignore] == 0} {
    puts "WARNING: This repository does not contain a master gitignore. creating one now."
    set target $master_gitignore
    set origin $script_dir/templates/hw.gitignore
    file copy -force $origin $target
}

puts "INFO: Project $proj_file has been checked into version control"