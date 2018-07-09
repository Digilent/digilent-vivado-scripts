# Check if vivado has an up-to-date bitstream. If so, call archive_project. Else, fail and tell user to generate and spot check.
puts "digilent_vivado_release not implemented in this commit"

# # Check if up-to-date bitstream exists
# set impl_needs_refresh get_property NEEDS_REFRESH [get_runs -filter "NAME==synth_1"]
# set synth_needs_refresh get_property NEEDS_REFRESH [get_runs -filter "NAME==impl_1"]
# set bitstream_file [glob -nocomplain [get_property DIRECTORY [get_runs -filter {NAME == impl_1}]]/*.bit]
# 
# if {synth_needs_refresh == 0 || impl_needs_refresh == 0 || bitstream_file == ""} {
# 	puts "ERROR: An up-to-date bitstream is required to generate a release"
# 	# exit
# }