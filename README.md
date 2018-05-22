When working with an existing repo containing this repo as a submodule:

	1. Clone the repository.
	
	2. Call the digilent-vivado-checkout.py script. This will source into digilent-vivado-checkout.tcl to create an XPR project in the <project>/proj directory.
	
	3. Open the XPR and make any hardware changes needed.
	
	4. Generate a bitstream.
	
	5. Export and Launch to SDK (Local to Project)
	
	6. Spot check project on board
	
	7. Close Vivado & SDK, then run digilent-vivado-checkin.py. This will collect all project sources that may have been added and place them into the proper directories.