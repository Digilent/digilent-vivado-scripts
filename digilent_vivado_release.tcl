# puts "digilent_vivado_release not implemented in this commit"

# ARGS:
#     -repo <repo>
#     -xpr <xpr> : path to project's xpr file, absolute or relative to current working directory

# if xpr is not specified:                                          $project = current_project
# if xpr is specified and the project specified by xpr is not open: $project = open_project <xpr>
# if xpr is specified and the project specified by xpr is open:     $project = current_project <project name>
# if -repo is not specified:                                        $repo = <xpr>/../.. (<repo>/proj/<xpr>)
# if -repo is specified:                                            $repo = <repo>

# Process -xpr flag
if {[info exists xpr] != 0} {unset xpr}
if {[info exists argv] != 0} {
    set xpr_idx [lsearch $argv "-xpr"]
    if {$xpr_idx != -1} {
        set xpr [lindex $argv [expr {$xpr_idx + 1}]]
    }
}
if {[info exists xpr] == 0} {
    set project [current_project]
} else {
    set projects [get_projects -filter DIRECTORY==[file dirname $xpr]]
    if {[llength $projects] == 1} {
        set project [current_project [lindex $projects 0]]
    } else {
        set project [open_project $xpr]
    }
}

# Process -repo flag
if {[info exists repo] != 0} {unset repo}
if {[info exists argv] != 0} {
    set repo_idx [lsearch $argv "-repo"]
    if {$repo_idx != -1} {
        set repo [lindex $argv [expr {$repo_idx + 1}]]
    }
}
if {[info exists repo] == 0} {
    set repo [file dirname [get_property DIRECTORY [current_project]]]
}

puts "Releasing project $project to repo $repo"

# Check if up-to-date bitstream exists
set impl_needs_refresh [get_property NEEDS_REFRESH [get_runs -filter "NAME==synth_1"]]
set synth_needs_refresh [get_property NEEDS_REFRESH [get_runs -filter "NAME==impl_1"]]
set bitstream_file [glob -nocomplain [get_property DIRECTORY [get_runs -filter {NAME == impl_1}]]/*.bit]

# Check if vivado has an up-to-date bitstream. If so, call archive_project. Else, fail and tell user to generate and spot check.
if {$synth_needs_refresh || $impl_needs_refresh || $bitstream_file == ""} {
 	puts "ERROR: An up-to-date bitstream is required to generate a release"
} else {
    set release_dir [file join ${repo} release]
    if {[file exists ${release_dir}] == 0} {file mkdir ${release_dir}}
    set archive [file join ${repo} release vivado_project.zip]
    set temp_dir [file join ${repo} release temp]
    if {[file exists ${temp_dir}] == 0} {file mkdir ${temp_dir}}
    archive_project ${archive} -temp_dir ${temp_dir} -force -include_local_ip_cache
    file copy -force ${bitstream_file} ${repo}/release/[file tail ${bitstream_file}]
    puts "Project released successfully"
}