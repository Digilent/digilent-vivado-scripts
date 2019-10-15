# Optional Arguments:
#     -r <repo_path>;   default=<digilent-vivado-scripts>/..; Git repo
#     -ws <ws_dir>;     default=<repo_path>/sdk; SDK workspace
#     -o <release_dir>; default=<repo_path>/release/temp/sdk_workspace_<time>; Directory to release files to

proc proc_sdk_release {argv} {
    # Handle repo_path argument
    set idx [lsearch ${argv} "-r"]
    if {${idx} != -1} {
        set repo_path [glob -nocomplain [file normalize [lindex ${argv} [expr {${idx}+1}]]]]
    } else {
        # Default
        set repo_path [file normalize [file join [file dirname [info script]] ..]]
    }

    # Handle ws_dir argument
    set idx [lsearch ${argv} "-ws"]
    if {${idx} != -1} {
        set ws_dir [glob -nocomplain [file normalize [lindex ${argv} [expr {${idx}+1}]]]]
    } else {
        # Default
        set ws_dir [file join ${repo_path} sdk]
    }
    
    # Handle release_dir argument
    set idx [lsearch ${argv} "-o"]
    if {${idx} != -1} {
        set release_dir [file normalize [lindex ${argv} [expr {${idx}+1}]]]
    } else {
        # Default
        set time [clock seconds]
        set release_dir [file join ${repo_path} release temp sdk_workspace_$time]]
    }

    # check that this script is not being run from vivado
    set tool [lindex [file split $::env(RDI_BASEROOT)] end]
    if {$tool != "SDK"} {
        return "ERROR: This script must be called from Xilinx SDK's XSCT Console"
    }

    # confirm that nothing will be overwritten
    if {[llength [glob -nocomplain [file join $release_dir *]]] != 0} {
        return "ERROR: directory $release_dir is not empty"
    }

    # confirm that the workspace actually exists
    if {[file exists $ws_dir] == 0} {
        return "ERROR: workspace $ws_dir does not exist"
    }

    # open the target workspace
    if {[getws] == $ws_dir} {
        if {[info exists old_ws]} {
            puts "WARNING: script unset the old_ws variable; original value='$old_ws'"
            unset old_ws
        }
    } elseif {[getws] == ""} {
        if {[info exists old_ws]} {
            puts "WARNING: script unset the old_ws variable; original value='$old_ws'"
            unset old_ws
        }
        setws $ws_dir
    } else {
        set old_ws [getws]; # used to return SDK to the workspace of origin
        setws -switch $ws_dir
    }

    # types of project in a workspace
    set types [list \
        "hw" \
        "bsp" \
        "app" \
    ]

    # patterns for files to be included in the release, listed by project type
    set patterns [list \
        "hw" \
        [list \
            *.hdf \
            *.bit \
            .project \
        ] \
        "bsp" \
        [list \
            .project \
            .cproject \
            .sdkproject \
            Makefile \
            *.mss \
        ] \
        "app" \
        [list \
            .project \
            .cproject \
            src \
        ]
    ]

    # copy files and directories that match the patterns into the release directory
    foreach type $types {
        foreach project [getprojects -type $type] {
            puts "Project \"${project}\":"
            set idx [lsearch $patterns $type]
            incr idx
            set project_release_dir [file join $release_dir $project]
            foreach pattern [lindex $patterns $idx] {
                set origins [glob -nocomplain [file join $ws_dir $project $pattern]]
                foreach origin $origins {
                    set target [file join $project_release_dir [file tail $origin]]
                    if {[file exists $release_dir] == 0} {
                        file mkdir $release_dir
                    }
                    if {[file exists $project_release_dir] == 0} {
                        file mkdir $project_release_dir
                    }
                    if {[file exists $target] && [file isdir $target]} {
                        return "ERROR: Cannot release $target as directory already exists"
                    } else {
                        file copy -force $origin $target
                        puts "    Released $target"
                    }
                }
            }
        }
    }

    # return to original workspace that called this script
    if {[info exists old_ws]} {
        setws -switch $old_ws
    }

    return "SUCCESS: Workspace successfully released"
}

set exit_message [proc_sdk_release $argv]
puts $exit_message

# # write return message
# set ase_log [file join $ws_dir [file tail [file rootname [info script]]].log]
# set fp [open $ase_log "w"]
# puts -nonewline $fp $exit_message
# close $fp