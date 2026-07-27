# Opens an existing (already built) Vivado project and exports a fixed,
# bitstream-included hardware platform (.xsa) to <repo>/hw_handoff.
#
# Usage:
#   set argv "-x <xpr_path>"
#   source export_xsa.tcl
#
# Optional: -o <name> overrides the output filename (<name>.xsa) instead of
# the default, which is named after the design's top module. Useful when
# multiple projects built from the same top module (e.g. different
# build-time variants of the same design) need distinct .xsa filenames so
# they don't overwrite each other in hw_handoff.
#
# Optional: -r <repo_path> overrides where <repo>/hw_handoff is created.
# Defaults to the xpr_path's grandparent directory (i.e. assumes
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
