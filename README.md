When working with an existing repo containing this repo as a submodule:

	1. Clone the repository.
	
	2. Use the git_vivado script's checkout subcommand to source into digilent-vivado-checkout.tcl to create an XPR project in the <project>/proj directory.
	
	3. Open the XPR and make any hardware changes needed.
	
	4. Generate a bitstream.
	
	5. Export and Launch to SDK (Local to Project)
	
	6. Spot check project on board
	
	7. Close Vivado & SDK, then use git_vivado's checkin subcommand to collect all project sources that may have been added and place them into the proper directories.
	
	8. Use git_vivado's release subcommand to generate a release ZIP archive and upload it to GiHub as a release.
