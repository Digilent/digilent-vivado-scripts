# export_xsa.tcl
#
# Export a fixed hardware platform (.xsa) with bitstream from a built project.
#
# Usage:
#   set argv "-x <xpr_path> [-o <name>] [-r <repo_path>]"
#   source export_xsa.tcl
#
# Arguments:
#   -x  project file, required
#   -o  output name (<name>.xsa), default is the top module;
#       gives build variants of one top module distinct files
#   -r  repo that holds hw_handoff, default is the grandparent of the xpr
#       (<repo>/proj/<project>.xpr); pass it for deeper projects such as
#       <repo>/proj/<variant>/<project>.xpr


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


# Export

puts "INFO: Opening project ${xpr_path}"
open_project -quiet ${xpr_path}

set top_module [get_property top [current_fileset]]
set handoff_dir [file join ${repo_path} hw_handoff]
if {[file exists ${handoff_dir}] == 0} {
    file mkdir ${handoff_dir}
}
if {${output_name} eq ""} {
    set output_name ${top_module}
}
set xsa_file [file join ${handoff_dir} "${output_name}.xsa"]

puts "INFO: Writing hardware platform to ${xsa_file}"
write_hw_platform -fixed -include_bit -force -file ${xsa_file}
puts "INFO: Wrote out xsa file ${xsa_file}"

close_project -quiet
