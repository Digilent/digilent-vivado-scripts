# Optional Arguments:
#     -r <repo_path>;     default=<digilent-vivado-scripts>/..; Git repo
#     -x <xpr_path>;      default=<repo_path>/proj/*.xpr;
#     -o <zip_path>;      default=<repo_path>/release/temp/vivado_project_<time>.zip; Output archive
#     -temp <temp_path>;  default=<repo_path>/release/temp/vivado_project_temp; Temporary directory to collect files to be archived in


# implementing this as a process allows returning on errors
proc proc_vivado_release {argv} {
    # Handle repo_path argument
    set idx [lsearch ${argv} "-r"]
    if {${idx} != -1} {
        set repo_path [file normalize [lindex ${argv} [expr {${idx}+1}]]]
    } else {
        # Default
        set repo_path [file normalize [file join [file dirname [info script]] ..]]
    }
    if {[file exists $repo_path] == 0} {
        return "ERROR: repo $repo_path does not exist"
    }

    # Handle xpr_path argument
    set idx [lsearch ${argv} "-x"]
    if {${idx} != -1} {
        set xpr_path [glob -nocomplain [file normalize [lindex ${argv} [expr {${idx}+1}]]]]
    } else {
        # Default
        set xpr_path [glob -nocomplain [file join ${repo_path} proj *.xpr]]
    }
    if {[llength ${xpr_path}] == 0} {
        return "ERROR: project not found"
    } else {
        set xpr_path [lindex ${xpr_path} 0]
    }
    if {[file exists $xpr_path] == 0} {
        return "ERROR: project $xpr_path does not exist"
    }

    # Handle zip_path argument
    set idx [lsearch ${argv} "-o"]
    if {${idx} != -1} {
        set zip_path [file normalize [lindex ${argv} [expr {${idx}+1}]]]
    } else {
        # Default
        set time [clock seconds]
        set zip_path [file join ${repo_path} release temp vivado_project_${time}.zip]
    }
    if {[file exists $zip_path]} {
        return "ERROR: archive $zip_path already exists"
    }

    # Handle temp_path argument
    set idx [lsearch ${argv} "-temp"]
    if {${idx} != -1} {
        set temp_path [file normalize [lindex ${argv} [expr {${idx}+1}]]]
    } else {
        # Default
        set temp_path [file join ${repo_path} release temp vivado_project_temp]
    }
    if {[llength [glob -nocomplain [file join $temp_path *]]] > 0} {
        return "ERROR: temp directory $temp_path contains files"
    }

    # Open the project
    set xpr_dir [file dirname $xpr_path]
    set xpr_name [file rootname [file tail $xpr_path]]
    set already_opened [get_projects -filter "DIRECTORY==$xpr_dir && NAME==$xpr_name"]
    if {[llength $already_opened] == 0} {
        open_project $xpr_path
    } else {
        current_project [lindex $already_opened 0]
    }
    puts "INFO: Releasing project [current_project]"

    # Check if the project has an up-to-date bitstream
    if {[get_property NEEDS_REFRESH [get_runs impl_1]]} {
        puts "WARNING: bitstream is not up-to-date; please generate a new one before publishing a release"
    }

    # resolve the archive name and archive the project
    # Note: archive_project automatically creates missing directories on passed paths
    archive_project $zip_path -temp_dir $temp_path -force -include_local_ip_cache
    puts "INFO: Released archive to $zip_path"

    return "Project successfully released"
}

set exit_message [proc_vivado_release $argv]
puts $exit_message
# # write exit message to log.
# set log_file [file join [file dirname $zip_path] "vivado_release_project_[clock seconds].log"]
# set fp [open $log_file "w"]
# puts -nonewline $fp $exit_message
# close $fp