set script_dir [file dirname [file normalize [info script]]]

# This script does nothing by default, edit it in your project repo to add functionality.
# Several comment blocks with examples can be seen below. Customize them as needed.
puts "INFO: Running [info script]"
puts "      This script is a stub. Nothing happened."


# # Exporting a bitstream for a hw-only project:
# puts "INFO: Running [info script]"
# puts [get_property directory [current_run]]; # impl_1
# set impl_dir [file join ${script_dir} proj *.runs impl_1]
# set src [glob [file join ${impl_dir} *.bit]]
# set release_dir [file join ${script_dir} release]
# if {[file exists ${release_dir}] == 0} {file mkdir ${release_dir}}
# set dst [file join ${release_dir} [file tail ${src}]]
# file copy -force ${src} ${dst}
# puts "INFO: Wrote out bitstream file ${dst}"


# # Exporting an xsa for a project with sw:
# puts "INFO: Running [info script]"
# set top_module [get_property top [get_filesets sources_1]]
# set handoff_dir [file join ${script_dir} hw_handoff]
# if {[file exists ${handoff_dir}] == 0} {file mkdir ${handoff_dir}}
# set xsa_file [file join ${handoff_dir} ${top_module}.xsa]
# write_hw_platform -fixed -include_bit -force -file ${xsa_file}
# puts "INFO: Wrote out xsa file ${xsa_file}"


# # Generate a release ZIP file for any project:
# set proj_name [get_property name [current_project]]
# set release_dir [file join ${script_dir} release]
# if {[file exists ${release_dir}] == 0} {file mkdir ${release_dir}}
# set zip_file [file join ${release_dir} ${proj_name}.xpr.zip]
# set temp_dir [file join ${script_dir} temp]
# archive_project ${zip_file} -temp_dir ${temp_dir} -force -include_local_ip_cache
# puts "INFO: Wrote out project release archive ${zip_file}"