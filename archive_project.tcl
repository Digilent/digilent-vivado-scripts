# Opens an existing Vivado project and archives it (sources, IP, board files)
# into a single ZIP under <repo>/release, using <repo>/temp as scratch space.
#
# Usage:
#   set argv "-x <xpr_path>"
#   source archive_project.tcl

set idx [lsearch ${argv} "-x"]
if {${idx} != -1} {
    set xpr_path [file normalize [lindex ${argv} [expr {${idx}+1}]]]
} else {
    puts "ERROR: -x <xpr_path> is required"
    exit 1
}

set repo_path [file normalize [file join [file dirname ${xpr_path}] ..]]

puts "INFO: Opening project ${xpr_path}"
open_project -quiet ${xpr_path}

set proj_name [get_property name [current_project]]
set release_dir [file join ${repo_path} release]
if {[file exists ${release_dir}] == 0} {
    file mkdir ${release_dir}
}
set temp_dir [file join ${repo_path} temp]
set zip_file [file join ${release_dir} "${proj_name}.xpr.zip"]

puts "INFO: Archiving project to ${zip_file}"
archive_project ${zip_file} -temp_dir ${temp_dir} -force -include_local_ip_cache
puts "INFO: Wrote out project release archive ${zip_file}"

close_project -quiet
