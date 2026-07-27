# Opens an existing Vivado project and archives it (sources, IP, board files)
# into a single ZIP under <repo>/release, using <repo>/temp as scratch space.
#
# Usage:
#   set argv "-x <xpr_path>"
#   source archive_project.tcl
#
# Optional: -o <name> overrides the output filename (<name>.xpr.zip) instead
# of the default, which is named after the project itself. Useful when
# multiple projects share the same project name (e.g. different build-time
# variants of the same design, each in its own subdirectory) and need
# distinct archive filenames so they don't overwrite each other in release.
#
# Optional: -r <repo_path> overrides where <repo>/release and <repo>/temp are
# created. Defaults to the xpr_path's grandparent directory (i.e. assumes
# <repo>/proj/<project>.xpr) when omitted; pass this explicitly if the
# project lives somewhere else under <repo> (e.g. nested one directory
# deeper, such as <repo>/proj/<variant>/<project>.xpr).

set idx [lsearch ${argv} "-x"]
if {${idx} != -1} {
    set xpr_path [file normalize [lindex ${argv} [expr {${idx}+1}]]]
} else {
    puts "ERROR: -x <xpr_path> is required"
    exit 1
}

set idx [lsearch ${argv} "-o"]
if {${idx} != -1} {
    set output_name [lindex ${argv} [expr {${idx}+1}]]
} else {
    set output_name ""
}

set idx [lsearch ${argv} "-r"]
if {${idx} != -1} {
    set repo_path [file normalize [lindex ${argv} [expr {${idx}+1}]]]
} else {
    set repo_path [file normalize [file join [file dirname ${xpr_path}] ..]]
}

puts "INFO: Opening project ${xpr_path}"
open_project -quiet ${xpr_path}

set proj_name [get_property name [current_project]]
if {${output_name} eq ""} {
    set output_name ${proj_name}
}
set release_dir [file join ${repo_path} release]
if {[file exists ${release_dir}] == 0} {
    file mkdir ${release_dir}
}
set temp_dir [file join ${repo_path} temp]
set zip_file [file join ${release_dir} "${output_name}.xpr.zip"]

puts "INFO: Archiving project to ${zip_file}"
archive_project ${zip_file} -temp_dir ${temp_dir} -force -include_local_ip_cache
puts "INFO: Wrote out project release archive ${zip_file}"

close_project -quiet
