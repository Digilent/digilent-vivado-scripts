# Note: argument order does not matter when setting argv; all arguments are optional
# Usage (No Defaults):
#   set argv "-r <repo_path> -x <xpr_path> -v <vivado_version> -w <workspace> -z <archive> -temp <temp_dir>"
#   source digilent_vivado_release.tcl
# Usage (All Defaults):
#   set argv ""
#   source digilent_vivado_release.tcl
# TODO: handle SDK projects.
# TODO: add debug flag for argument checking

puts "digilent_vivado_release not implemented in this commit"

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

# Handle workspace argument
set idx [lsearch ${argv} "-w"]
if {${idx} != -1} {
	set workspace_path [glob -nocomplain [file normalize [lindex ${argv} [expr {${idx}+1}]]]]
} else {
	# Default
	set workspace_path [glob -nocomplain [file join ${repo_path} sdk]]
}
if {[llength ${workspace_path}] != 1} {
	puts "ERROR: Workspace not found"
} else {
	set workspace_path [lindex ${workspace_path} 0]
}

# Handle archive argument
set idx [lsearch ${argv} "-z"]
if {${idx} != -1} {
	set archive [file normalize [lindex ${argv} [expr {${idx}+1}]]]
} else {
	# Default
	set archive [file join ${repo_path} release [file tail ${repo_path}].zip]
    # TODO: add numeric suffix until the "already exists" check passes
}
if {[llength [glob -nocomplain ${archive}]] > 0} {
	puts "ERROR: Archive already exists"
}

# Handle temp_dir argument
set idx [lsearch ${argv} "-temp"]
if {${idx} != -1} {
	set temp_dir [file normalize [lindex ${argv} [expr {${idx}+1}]]]
} else {
	# Default
	set temp_dir [file join ${repo_path} release temp]
    # TODO: add numeric suffix until the "already exists" check passes
}
if {[llength [glob -nocomplain ${temp_dir}]] > 0} {
	puts "ERROR: Temp Directory already exists"
}

puts "repo_path: $repo_path"
puts "xpr_path: $xpr_path"
puts "vivado_version: $vivado_version"
puts "workspace_path: $workspace_path"
puts "archive: $archive"
puts "temp_dir: $temp_dir"




# ARGS:
#     -repo <repo>
#     -xpr <xpr> : path to project's xpr file, absolute or relative to current working directory
# if -xpr is not specified:                                          $project = current_project
# if -xpr is specified and the project specified by xpr is not open: $project = open_project <xpr>
# if -xpr is specified and the project specified by xpr is open:     $project = current_project <project name>
# if -repo is not specified:                                        $repo = <xpr>/../.. (<repo>/proj/<xpr>)
# if -repo is specified:                                            $repo = <repo>

# # Process -xpr flag
# if {[info exists xpr] != 0} {unset xpr}
# if {[info exists argv] != 0} {
#     set xpr_idx [lsearch $argv "-xpr"]
#     if {$xpr_idx != -1} {
#         set xpr [lindex $argv [expr {$xpr_idx + 1}]]
#     }
# }
# if {[info exists xpr] == 0} {
#     set project [current_project]
# } else {
#     set projects [get_projects -filter DIRECTORY==[file dirname $xpr]]
#     if {[llength $projects] == 1} {
#         set project [current_project [lindex $projects 0]]
#     } else {
#         set project [open_project $xpr]
#     }
# }
# 
# # Process -repo flag
# if {[info exists repo] != 0} {unset repo}
# if {[info exists argv] != 0} {
#     set repo_idx [lsearch $argv "-repo"]
#     if {$repo_idx != -1} {
#         set repo [lindex $argv [expr {$repo_idx + 1}]]
#     }
# }
# if {[info exists repo] == 0} {
#     set repo [file dirname [get_property DIRECTORY [current_project]]]
# }
# 
# puts "Releasing project $project to repo $repo"
# 
# # Check if up-to-date bitstream exists
# set impl_needs_refresh [get_property NEEDS_REFRESH [get_runs -filter "NAME==synth_1"]]
# set synth_needs_refresh [get_property NEEDS_REFRESH [get_runs -filter "NAME==impl_1"]]
# set bitstream_file [glob -nocomplain [get_property DIRECTORY [get_runs -filter {NAME == impl_1}]]/*.bit]
# 
# # Check if vivado has an up-to-date bitstream. If so, call archive_project. Else, fail and tell user to generate and spot check.
# if {$synth_needs_refresh || $impl_needs_refresh || $bitstream_file == ""} {
#  	puts "ERROR: An up-to-date bitstream is required to generate a release"
# } else {
#     set release_dir [file join ${repo} release]
#     if {[file exists ${release_dir}] == 0} {file mkdir ${release_dir}}
#     set archive [file join ${repo} release vivado_project.zip]
#     set temp_dir [file join ${repo} release temp]
#     if {[file exists ${temp_dir}] == 0} {file mkdir ${temp_dir}}
#     archive_project ${archive} -temp_dir ${temp_dir} -force -include_local_ip_cache
#     file copy -force ${bitstream_file} ${repo}/release/[file tail ${bitstream_file}]
#     puts "Project released successfully"
# }