# Digilent Vivado Scripts

## Introduction
This repository contains a set of scripts for creating, maintaining, and releasing git repositories containing minimally version-controlled Vivado and Xilinx SDK projects. These scripts have only been tested with Vivado 2018.2; they may or may not work with newer or older versions of Vivado. A Python 3.6.3 (or newer) installation is required to use these scripts. As of time of writing, no additional Python modules 

----------------
## Python Frontend
A front-end script, git_vivado.py, is provided to parse command line arguments and call into Vivado at the command line.  This script has three subcommands: "checkout", "checkin", and "release". Each of these subcommands has its own help menu, which explains the arguments that can be passed to the script, as well as show what the default values of each of these arguments will be. All paths passed to the script are assumed to be relative to the current working directory.

**Note**: *Each script can instead be manually sourced within the TCL console in Vivado. When doing so, take care to properly set the `argv` variable, as described in each scripts' Example Usage subsection*

--------------
## Commands / Scripts
### Checkout
#### Description
This subcommand calls into digilent_vivado_checkout.tcl in order to create a Vivado project, in the form of an XPR file, using the sources and scripts contained in the project repository. If a hardware handoff file and SDK projects are present in the repository, the SDK workspace is initialized in the specified workspace directory.
#### Optional Arguments
1. `-r <repo>`: Path to the repository directory. Default: `<digilent-vivado-scripts>/..`
1. `-x <xpr>`: Path to the project .xpr file the repo is to be checked out into. Default: `<repo>/proj/<repo name>.xpr`
1. `-w <workspace>`: Path to the directory to be used as the SDK workspace. Default: `<repo>/sdk`
1. `-v <version>`: Vivado version number. Default contained in config.ini. (Python only)

**Note**: *All paths passed as arguments must either be absolute or relative to the current working directory.*
#### Example Usage
##### Python:
> <code>python git_vivado.py checkout -r D:/Github/Zybo-Z7-10-HDMI</code>

##### TCL:
> <code>set argv "-r D:/Github/Zybo-Z7-10-HDMI"</code>

> <code>source digilent-vivado-checkout.tcl</code>

-----------
### Checkin
#### Description
This subcommand calls into digilent_vivado_checkin.tcl in order to collect sources and generate needed scripts from a Vivado project into the repository structure described below. Files required for checkout *that are not already present* in the repository (such as project_info.tcl and gitignores), are automatically created. These files are not overwritten if they already exist.
#### Optional Arguments
1. `-r <repo>`: Path to the repository directory. Default: `<digilent-vivado-scripts>/..`
1. `-x <xpr>`: Path to the project .xpr file to be processed for checkin. Default: `<repo>/proj/*.xpr`
1. `-w <workspace>`: Path to the SDK workspace associated with the project. If non-default, the workspace is copied to `<repo>/sdk`. Default: `<repo>/sdk`
1. `-no_hdf`: Flag used to prevent overwriting of the hardware handoff. If this flag is not present and the bitstream is up-to-date, the hardware handoff file is checked in to `<repo>/hw_handoff`
1. `-v <version>`: Vivado version number. Default contained in config.ini. (Python only)

**Note**: *All paths passed as arguments must either be absolute or relative to the current working directory.*
#### Example Usage
##### Python:
> <code>python git_vivado.py checkin -r D:/Github/Zybo-Z7-10-HDMI</code>

##### TCL:
> <code>set argv "-r D:/Github/Zybo-Z7-10-HDMI"</code>

> <code>source digilent-vivado-checkin.tcl</code>

-----------
### Release
#### Description
This subcommand collects all required files and produces a release ZIP archive. It cannot be run from the TCL Console, as Python is required to manage zipping and unzipping of files. A release consists of the repo's README, an archived Vivado project, with XPR and all dependencies, and the SDK workspace. The Vivado project must have an up-to-date bitstream in order for the release to be generated.
#### Optional Arguments
1. `-r <repo>`: Path to the repository directory. Default: `<digilent-vivado-scripts>/..`
1. `-x <xpr>`: Path to the project .xpr file to be released. Default: `<repo>/proj/*.xpr`
1. `-w <workspace>`: Path to the SDK workspace associated with the project. Default: `<repo>/sdk`
1. `-z <archive>`: Path where the resulting ZIP file will be placed. Default: `<repo>/release/<repo name>-<version>-#.zip`
1. `-temp <temp_dir>`: Path to a safe place to put temporary files. Default: `<repo>/release/temp`
1. `-v <version>`: Vivado version number. Default contained in config.ini. (Python only)

**Note**: *All paths passed as arguments must either be absolute or relative to the current working directory.*
#### Example Usage
##### Python:
> <code>python git_vivado.py release -r D:/Github/Zybo-Z7-10-HDMI</code>

##### TCL:
> <code>set argv "-r D:/Github/Zybo-Z7-10-HDMI"</code>

> <code>source digilent-vivado-release.tcl</code>

------------------------------------
## Other Files and Overall Structure
### Configuration File
The digilent-vivado-scripts repository contains a file named "config.ini". This file contains several values used by the Python frontend to determine what the default arguments for the different subcommands should be. It has not yet been decided how this file should be managed/version-controlled. See "Known Issues" at the bottom of this document for a little more information.

### Repository Structure
In order to ensure that any changes to this repository do not break the projects that use them, it is expected that this repository will be used as a submodule of each project repository that is intended to use them.

* **\<project repo\>/digilent-vivado-scripts**: Submodule containing the scripts described by this document.
* **\<project repo\>/hw_handoff**: Used to contain the hardware handoff file.
* **\<project repo\>/proj**: Used to contain a checked-out Vivado project.
* **\<project repo\>/release**: Contains temporary files necessary to generate a release zip archive.
* **\<project repo\>/repo**: Contains local IP, IP submodules, and cached generated sources.
* **\<project repo\>/sdk**: Contains SDK projects, and is the workspace used with SDK.
  * **\<repo\>/sdk/.gitignore**: File describing which SDK files should be version controlled. Template generated by the checkin script.
* **\<project repo\>/src**: Contains source files for the Vivado Project.
  * **\<project repo\>/src/bd**: Contains a TCL script used to re-create a block design.
  * **\<project repo\>/src/constraints**: Contains XDC constraint files.
  * **\<project repo\>/src/hdl**: Contains Verilog and VHDL source files.
  * **\<project repo\>/src/ip**: Contains XCI files describing IP to be instantiated in non-IPI projects.
  * **\<project repo\>/src/others**: Contains all other required sources, such as memory initialization files.
* **\<project repo\>/.gitignore**: File describing which sources should be version controlled. Template is generated by the checkin process.
* **\<project repo\>/.gitmodules**: File describing submodules of the repository. Automatically maintained by the "git submodule" command.
* **\<project repo\>/project_info.tcl**: Script generated by first-time checkin used to save and re-apply project settings like board/part values. This can be modified after initial creation to manually configure settings that are not initially supported. **Note**: *This script should be deleted and recreated when porting a project from one board to another.*
* **\<project repo\>/README.md**: Markdown file describing the project and the process needed to use it, from downloading the release archive, to programming the FPGA.

------------
## Workflows
### 1. Creating a New Project
1. Create a folder on your computer to hold the project repository. Use the naming convention <code>\<board\>-\<variant\>-\<project name\></code> (for example: "Zybo-Z7-20-DMA"). This folder will be referred to as the "local repo"

2. Create a repository on GitHub for your project with Digilent as the owner. Name it the same as the local repo folder. Do not have Github create a README, gitignore file, or license for you. This repository will be referred to as the "remote repo".

3. In a command line interface (git bash is recommended) cd into the local repo. Call the following set of commands, in order to initialize the repository, add these scripts to it, and set its remote.
    * <code>git init</code>
    * <code>git submodule add https://github.com/Digilent/digilent-vivado-scripts</code>
    * <code>git remote add origin \<remote repo URL\></code>

4. While creating and developing your project using Vivado and Xilinx SDK, there are a few guidelines to follow:
    * When creating the project, make sure to place the Vivado project in a folder named "proj" in the local repo.
    * When exporting hardware to SDK, make sure to export to a folder named "hw_handoff" in the local repo. **Note**: *The checkin command, used in (5), below will also handle exporting the hardware handoff.*
    * When launching SDK, make sure to set the Exported Location as the hw_handoff folder, and the Workspace as a folder named "sdk" in the local repo.
    * If IPs or interfaces from [vivado-library](https://github.com/Digilent/vivado-library) are required, create a folder called "repo" in the local repo, and add vivado-library as a submodule within that folder.

5. Call the command below. This command can be called from anywhere in your filesystem, with relative paths changed as required. Missing required folders and files are automatically created, including gitignores. **Note:** *Invoking the script in this way uses all default arguments, which assume that the local repo directory structure is used. See "Creating a Repo from a Local Project", below, for an alternate method.*
    * <code>python ./digilent_vivado_scripts/git_vivado.py checkin</code>

6. Create a README for the repo that specifies what the project is supposed to do and how to use a release archive for it. See "Using a Release Archive", below, and the file "template_README.md in digilent-vivado-scripts for more information.

7. Add, commit, and push your changes to the remote repo:

    * <code>git add .</code>
    * <code>git commit -m "Initial Commit"</code>
    * <code>git push origin master</code>

8. Create and upload a release ZIP to Github - see "Creating a Release Archive" below.

----
### 2. Creating a Repo from a Local Project
If your new project was not created following the directory structure described in "Creating a Repo from a Local Project", above, this is the workflow to follow. This flow is a little more in depth. It assumes that a project (and SDK workspace) has already been created.

1. Create a repository on GitHub for your project with Digilent as the owner. Name it the same as the local repo folder. Do not have Github create a README, gitignore file, or license for you. This repository will be referred to as the "remote repo". Clone this repository to your computer - the folder where the repository is placed will be referred to as the "local repo".
    * <code>cd \<intended parent directory of the local repo\></code>
    * <code>git clone --recursive \<remote repo URL\></code>

2. In a command line interface (git bash is recommended) cd into the local repo. Call the following command in order add these scripts to the repository.
    * <code>git submodule add https://github.com/Digilent/digilent-vivado-scripts</code>

3. Use the checkin command of git_vivado.py to check the local project into the local repo, adding required folders, required files, and the projects sources:
    * <code>cd digilent-vivado-scripts</code>
    * <code>python git_vivado.py checkin -x \<path to local project's .xpr file\> -w \<path to local project's SDK workspace\></code>
    * <code>cd ..</code>

4. If any changes need to be made to the project during the checkout process, the project_info.tcl generated by the checkin command should be manually edited.

6. Create a README for the repo that specifies what the project is supposed to do and how to use a release archive for it. See "Using a Release Archive", below, and the file "template_README.md in digilent-vivado-scripts for more information.

5. Add, commit, and push your changes to the remote repo:
    * <code>git add .</code>
    * <code>git commit -m "Initial Commit"</code>
    * <code>git push origin master</code>

6. Create and upload a release ZIP to Github - see "Creating a Release Archive" below.


----
### 3. Retargeting an Existing Repo to use these Scripts
1. Clone (or pull) the Vivado project to be retargeted. Use its existing version control system to generate an XPR. If relevant, make sure to call "git submodule init" followed by "git submodule update" from a command line interface (git bash is recommended for Windows) from within the repo directory.

2. Open the project in Vivado and make any changes necessary (perhaps upgrading IP). When exporting to and launching SDK, make sure to use exported locations and workspaces that are not "Local to Project".

3. Clone the project repository again in a different location. Remove all files from this directory.

4. In a command line interface (git bash) cd into the clean repository directory. Call the following command: 
    * <code>git submodule add https://github.com/Digilent/digilent-vivado-scripts</code>

5. Use the checkin command of git_vivado.py to check the project into the clean local repo, adding required folders, required files, and the projects sources:
    * <code>python <path to digilent-vivado-scripts>/git_vivado.py checkin -x \<path to checked out project's .xpr file\> -w \<path to checked out project's SDK workspace\></code>

6. If any changes need to be made to the project during the checkout process, the project_info.tcl generated by the checkin command should be manually edited.

7. If required, copy all files from the project's SDK workspace into the repo's "sdk" folder.

8. Create a README for the repo that specifies what the project is supposed to do and how to use a release archive for it. See "Using a Release Archive", below, and the file "template_README.md in this submodule for more information. <code>FIXME: create template</code>

9. Add, commit, and push your changes to the remote repo:
    * <code>git add .</code>
    * <code>git commit -m "Initial Commit"</code>
    * <code>git push origin master</code>

10. Create and upload a release ZIP to Github - see "Creating a Release Archive" below.

----
### 4. Making Changes to a Project that uses this Submodule
1. Clone the Vivado project to be changed. **Note**: *Pull the repo instead, if you already have a local instance of the project.*
    * <code>git clone --recursive \<remote repo URL\></code>

2. In a command line interface (git bash is recommended for Windows) cd into the local project.

**NOTE**: Steps 3, 4, and 5 are only required if changes to the Vivado project are required.

3. Call the command below. This command can be called from anywhere in your filesystem, with the relative path to git_vivado. This will also create a gitignore file for the repository. Default arguments will create the XPR at "\<project repo\>/proj/\<project name\>.xpr".
    * <code>python \<path to digilent-vivado-scripts\>/git_vivado.py checkout</code>

4. Open the project in Vivado and make any changes necessary (perhaps upgrading IP or fixing a bug). When exporting to and launching SDK, make sure to use the local repo's "hw_handoff" folder for the exported location and "sdk" folder for the workspaces.

5. Call the command below. This command can be called from anywhere in your filesystem, with the relative path to git_vivado changed as required. Default arguments are fine, as they assume the use of the "proj" and "sdk" folders. Add the `-no_hdf` flag if you do not wish to overwrite the hardware handoff file.
    * <code>python \<path to digilent-vivado-scripts\>/git_vivado.py checkin</code>

6. Open Xilinx SDK, using the local repo's "sdk" folder as it's workspace. 

    **Important**: *If this is your first time cloning this repo, and there are projects in the sdk folder, you will need to initialize the workspace by launching SDK directly, rather than through Vivado. Launching from Vivado may create a duplicate hardware platform.*

    If you already had an instance of the project on your system, you may only need to open SDK with the local repo's "sdk" folder as the workspace.

    If the hardware handoff file has changed since the workspace was first initialized, you may need to right click on the hw_platform project and select "Change Hardware Specification" in order to point it to the hw_handoff folder's .hdf file.

    Projects that have been added to the repository since it was initialized (all projects, if the repo was just cloned) must be imported into the workspace, by selecting *File -> Import*, then navigating the dialog to select "Existing Projects into Workspace" from the local repo's "sdk" folder.

7. Make sure to update the repo's README as required.

8. Add, commit, and push your changes.
    * <code>git add .</code>
    * <code>git commit -m "Initial Commit"</code>
    * <code>git push origin master</code>

9. Create and upload a release ZIP to GitHub - see "Creating a Release Archive" below.

----
### 5. Creating a Release Archive
1. If a README has not been created for the repo, first create one.

2. Open the repo's Vivado project, and make sure that the bitstream is up to date and that hardware has been exported to the hw_handoff folder (if applicable).

3. Open the repo's SDK workspace, and make sure that the project builds fully and is functional.

4. If the Vivado project is located in the local repo's proj folder, and the SDK workspace is located in the local repo's sdk folder, the command below can be used with all default arguments to create a release zip archive. By default the output ZIP file will be placed in a release_# folder of the local repo (which is ignored by the version control system).
    *  <code>python \<path to digilent-vivado-scripts\>/git_vivado.py release</code>

**NOTE** *The python script is required to stitch together files released by Vivado and SDK. It calls into digilent_vivado_release.tcl and digilent_sdk_release.tcl. When sourced in Vivado's TCL console (vivado_release), or SDK's XSCT console (sdk_release), these TCL scripts can still be used to create the individual components of a release.*

5. Take the ZIP archive output by the script, and add a minor version number to its name, such that the name follows the pattern: "\<project name\>-\<vivado version number\>-\<minor version number\>.zip" (for example "Zybo-Z7-20-DMA-2018.2-3.zip").

6. Draft a new release on Github and upload the ZIP to it. Give the release a descriptive title including the name of the project and the tool version number it supports. Use the format "v\<vivado version number\>-\<minor version number\>" for the version tag. Add text specifying the name of the ZIP that the user must download to the release's description field.

----
### 6. Using a Release Archive
1. Download and extract the most recent release archive from the repository's releases page.
2. Open the project in the version of Vivado specified by the README, by using the "Open Project" dialog and selecting the project's .xpr file.
#### Vivado Only
3. The Vivado project will already have a bitstream generated, open the Hardware Manager, connect to your board, and program it.
#### Vivado + Xilinx SDK
3. Launch Xilinx SDK, selecting the sdk_workspace folder of the extracted release for the SDK workspace.
4. Use the File->Import dialog to import all projects from the sdk_workspace folder into the workspace.
5. Right click on the application project's src folder and select "Import". Import all files from \<extracted location\>/sdk_appsrc, overwriting anything that already exists.
6. Use the Xilinx->Program dialog and Run option in the application project's right-click menu to program the board and run the application on it.
7. If changes are later made to the Vivado design, the SDK hardware platform must be changed to reflect the Vivado changes: After generating a bitstream, use Vivado's *File->Export->Export Hardware* dialog to create a handoff file. Then, in SDK, right click on the hardware platform project and select *Change Hardware Specification* to point the hardware platform to the new handoff file.

----
### Appendix: Using the TCL Scripts from the TCL Console

Each TCL script in this repository can be sourced from the TCL (or XSCT) console in the appropriate tool. "digilent_vivado_\*" scripts can only be sourced from Vivado, while "digilent_sdk_\*" scripts can only be sourced from SDK's XSCT console (Xilinx->XSCT in the SDK GUI). Arguments are passed to these scripts through the use of the `argv` variable. Care should be taken to ensure that the wrong arguments are not passed to these scripts.

Sourcing a script and passing all default arguments can be accomplished in the following way:
* <code>set argv ""</code>
* <code>source \<path to digilent-vivado-scripts\>/\<script name\>.tcl</code>

An example of  passing non-default arguments (checking in a local "My_Project" to a local "My_Repo"):
* <code>set argv "-r C:/My_Repo -x C:/My_Project/My_Project.xpr -w C:/My_Project/My_Project.sdk"</code>
* <code>source digilent_vivado_checkin.tcl</code>

----
## Known Issues
* Each developer needs their own version of the configuration file, config.ini, for each project they are woking on. The configuration file should be moved to somewhere outside of the repo submodule to accomodate this, in a predictable location on Linux and Windows. The python script will need to be updated to accomodate this, a location and less generic name will need to be chosen for the configuration file.
* The "archive project" functionality of Vivado may include local SDK sources in the release archive. This should be avoided so that users have a clean workspace to Export and Launch SDK into. The current process requires that the project's SDK workspace is created external to the Vivado project.
* There is some danger that modifications to Digilent's board files may break existing projects, it may be worth considering adding the vivado-boards repository as a submodule to project repositories.
* Releases do not contain a hardware handoff, requiring that the user open Xilinx SDK directly, rather than through Vivado.
