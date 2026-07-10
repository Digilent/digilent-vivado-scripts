# Opens an existing (already built) Vivado project and exports a fixed,
# bitstream-included hardware platform (.xsa) to <repo>/hw_handoff.
#
# Usage:
#   set argv "-x <xpr_path>"
#   source export_xsa.tcl

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

set top_module [get_property top [current_fileset]]
set handoff_dir [file join ${repo_path} hw_handoff]
if {[file exists ${handoff_dir}] == 0} {
    file mkdir ${handoff_dir}
}
set xsa_file [file join ${handoff_dir} "${top_module}.xsa"]

puts "INFO: Writing hardware platform to ${xsa_file}"
write_hw_platform -fixed -include_bit -force -file ${xsa_file}
puts "INFO: Wrote out xsa file ${xsa_file}"

close_project -quiet
