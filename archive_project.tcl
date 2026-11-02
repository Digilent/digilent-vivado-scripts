# archive_project.tcl
#
# Archive a project (sources, IP, board files) into one ZIP under <repo>/release.
#
# Usage:
#   set argv "-x <xpr_path> [-o <name>] [-r <repo_path>] [-t <temp_dir>]"
#   source archive_project.tcl
#
# Arguments:
#   -x  project file, required
#   -o  output name (<name>.xpr.zip), default is the project name;
#       gives build variants that share a project name distinct files
#   -r  repo that holds release and temp, default is the grandparent of the
#       xpr (<repo>/proj/<project>.xpr); pass it for deeper projects such as
#       <repo>/proj/<variant>/<project>.xpr
#   -t  scratch directory, default <repo>/temp;
#       needed when archiving projects in parallel, since variants of one
#       design would otherwise stage into the same path


# Helpers

# Return the value following flag in argv, or default when flag is absent
proc arg_value {flag default} {
    global argv
    set idx [lsearch ${argv} ${flag}]
    if {${idx} == -1} {
        return ${default}
    }
    return [lindex ${argv} [expr {${idx}+1}]]
}


# Arguments

set xpr_path [arg_value "-x" ""]
if {${xpr_path} eq ""} {
    puts "ERROR: -x <xpr_path> is required"
    exit 1
}
set xpr_path [file normalize ${xpr_path}]

set output_name [arg_value "-o" ""]
set repo_path [file normalize [arg_value "-r" [file join [file dirname ${xpr_path}] ..]]]


# Archive

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
set temp_dir [file normalize [arg_value "-t" [file join ${repo_path} temp]]]
set zip_file [file join ${release_dir} "${output_name}.xpr.zip"]

puts "INFO: Archiving project to ${zip_file} (scratch: ${temp_dir})"
archive_project ${zip_file} -temp_dir ${temp_dir} -force -include_local_ip_cache
puts "INFO: Wrote out project release archive ${zip_file}"

close_project -quiet
