# Digilent Vivado Scripts

## Introduction
This repository contains a set of scripts for creating, maintaining, and releasing git repositories containing minimally version-controlled Vivado and Xilinx SDK projects. A Python 3.6.3 (or newer) installation is required to use the Python frontend for these scripts. As of time of writing, no additional Python modules are depended on.

----------------
## Quick Guide

This guide covers only what is required to gain access to and build demo project sources. For more in-depth details on these steps, and for information on how to push changes to a demo repository or build a release, see the **Workflows** section of this document, below.

### Prerequisites
- You must have the URL for a demo repository that uses digilent-vivado-scripts as a submodule. 
  
    For the purposes of this guide, any time that the text `<demo>` appears, you should replace it with the name of your chosen demo, as it appears at the end of the URL. For example, for the [Zybo Z7-20 HDMI demo](https://github.com/Digilent/Zybo-Z7-20-HDMI), `<demo>` should be replaced with `Zybo-Z7-20-HDMI`.
- Make sure that [Git](https://git-scm.com/) and a console application that can use it are installed on your computer. Most Linux systems will already have git installed. Windows users are recommended to use the Git Bash shell available through https://gitforwindows.org.
- Make sure you have the version of Vivado and/or Xilinx SDK targeted by your chosen demo repository installed on your computer. The README for your chosen demo will describe which version of these tools it can be used with. Installation instructions can be found in the [Installing Vivado, Xilinx SDK, and Digilent Board Files](https://reference.digilentinc.com/vivado/installing-vivado/start) guide on the Digilent Wiki.
### Getting Demo Sources
1. Open your git-compatible console or terminal application.
1. Change directory (using the `cd` command) to the folder that you wish to put the demo sources into. **Note:** *Take note of which directory you are in, it will be used again later*
1. Clone the chosen demo repository. Since the demo repository uses submodules, you should specify the --recursive flag when cloning:
  
    `git clone --recursive https://github.com/Digilent/<demo>`
1. *Only if* the chosen demo repository uses multiple branches to contain multiple demos - which is described in the repository's README - then use the steps below to get the correct sources for that branch.
    1. Change the working directory to the folder the repo was cloned into:
    
        `cd <demo>`
    1. If you don't know if your chosen demo repository contains multiple demo branches, or if you don't know the name of the demo branch you want to check out, the following command can be used to list all available branches:
  
        `git branch -a`
  1. Check out the branch for the demo you wish to access:

        `git checkout <demo branch>`
  1. When checking out a branch, make sure to run the following commands. This will make sure that the correct versions are used for any sources that are included in the demo as submodules.
    
        `git submodule init`

        `git submodule update`
### Initializing and Building the Vivado Project
1. Launch the version of Vivado that your chosen demo targets.
1. Once Vivado is open, open the TCL Console at the bottom of the screen.
1. To initialize and open the Vivado project, run the following command in the TCL console, changing `<path>` to match the location of the directory that you noted down in Step 2 of the *Getting Demo Sources* section:

    `set argv ""; source <path>/<demo>/digilent-vivado-scripts/digilent_vivado_checkout.tcl`
1. At this point you now have access to the Vivado Project and all of its sources. The project can be viewed, changes can be made, a bitstream can be generated, and hardware handoff file (HDF) can be generated. For Standalone Hardware demos, the Quick Guide ends here. The introduction of the next section will tell you how to determine whether your chosen demo is a Standalone Hardware demo or not.
### Initializing and Building the SDK Workspace
Not all demos contain a Xilinx SDK workspace. You can tell the difference by checking to see if an `sdk` folder is present in the cloned demo's folder. Some demos may have their SDK workspaces broken out into a seperate `*-SW` repo, included as a submodule of a "root" repository. If this folder or other repository does not exist, then this section can be skipped. 
1. Launch the version of Xilinx SDK that your chosen demo targets. It is important that you launch SDK directly, **not** through Vivado, to avoid creating an additional hardware platform before the one found in the demo repository can be added to the workspace.
1. When SDK launches, you will be prompted to select a directory as a workspace. Select the demo repository's `sdk` folder, then click **OK**. For example, the Zybo-Z7-20-HDMI repository would use the folder `<path>/<demo>/sdk` as its workspace, where `<path>` is the working directory that you noted down in Step 2 of the *Getting Demo Sources* section. Make sure to leave the *Use this as the default...* box unchecked.
1. When the SDK window fully opens, click the **Import Project** button. This will launch a dialog that will be used to bring in all projects from the demo repository.
    * **Browse** to select the `<path>/<demo>/sdk` folder as the root directory.
    * Make sure that all of the projects that are present (and not grayed out) are selected.
    * All other options can be left as defaults.
    * When satified that the correct projects will be brought into the workspace, click **Finish**.
1. When the projects are imported, the workspace will be built automatically. If errors are present, you may need to find the board support package project (named `*_bsp`) in the *Project Explorer*, right click on it, and select **Regenerate BSP Sources**. Upon doing so, the workspace will be rebuilt, and the errors should resolve themselves.
1. Check your demo repository's README for additional requirements. Some demos may require additional configuration, such as setting environment variables that depend on where the demo repository is located on your computer.
1. At this point you now have access to the Xilinx SDK Workspace and all of its sources. The sources can be viewed, changed, rebuilt, and the application project can be run on your board.
### Importing a Modified Hardware Design to SDK
After setting up the Vivado Project and SDK Workspace, a link should be created so that changes made to the hardware design can be automatically imported into the software workspace. **Note:** *These steps are intended for Baremetal Software projects. If the demo is a Petalinux Software or Standalone Hardware project, then this section should not be used. The steps required to handle bringing changes to hardware into a Petalinux Software project will be covered in other documentation associated with that project.*
1. In Vivado, with the demo's project open, click the **Generate Bitstream** button at the bottom of the *Flow Navigator* pane. This will fully build the project, through Synthesis and Implementation, and may take some time, typically 5 to 30+ minutes, depending on the complexity of the design and the specifications of your computer.
1. Once the bitstream has been generated, in the menu at the top of the screen, use the **File > Export > Export Hardware** option to export the generated Hardware Handoff (HDF) file:
    * In the dialog, click the **...** button to select the `<path>/<demo>/hw_handoff` folder, `<path>` is the working directory that you noted down in Step 2 of the *Getting Demo Sources* section.
    * Make sure that the *Include Bitstream* box is checked.
    * Once satisied that the options are correct, click **OK** to export the hardware handoff file.
    * If prompted, overwrite the existing file.
1. In Xilinx SDK, find the hardware platform project (named `*_hardware_platform_0`) in the *Project Explorer*, right click on it, and select **Change Hardware Platform Specification**. This will launch a dialog which you can use to point SDK to the exported HDF file:
    * Browse to and select the HDF file in the `<path>/<demo>/hw_handoff` folder (the same folder as selected for export in Step 2 of this section).
    * Once satisied that the correct file is specified, click **OK** to export the hardware handoff file.
1. In future, whenever exporting hardware from Vivado, use the same `<path>/<demo>/hw_handoff` folder. With the specification chosen, whenever you do so, Xilinx SDK will prompt you to choose whether to automatically import the new HDF or not.
### Final Notes
At this point, you have access to a working copy of the demo repository. The chosen demo's README or wiki page will contain instructions on how to use this demo once it is programmed onto your board.

For technical support, please visit the [Digilent Forums](https://forum.digilentinc.com/forum/4-fpga).

This concludes the *Quick Guide*. The remainder of this document discusses the implementation of the digilent-vivado-scripts repository and how to use the scripts in more technical detail.

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
> `python3 git_vivado.py checkout -r D:/Github/Zybo-Z7-10-HDMI`

##### TCL:
> `set argv "-r D:/Github/Zybo-Z7-10-HDMI"`

> `source digilent-vivado-checkout.tcl`

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
> `python3 git_vivado.py checkin -r D:/Github/Zybo-Z7-10-HDMI`

##### TCL:
> `set argv "-r D:/Github/Zybo-Z7-10-HDMI"`

> `source digilent-vivado-checkin.tcl`

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
> `python3 git_vivado.py release -r D:/Github/Zybo-Z7-10-HDMI`

##### TCL:
> `set argv "-r D:/Github/Zybo-Z7-10-HDMI"`

> `source digilent-vivado-release.tcl`

------------------------------------
## Other Files and Overall Structure
### Configuration File
The digilent-vivado-scripts repository contains a file named `config.ini`. This file contains several values used by the Python frontend to determine what the default arguments for the different subcommands should be. It has not yet been decided how this file should be managed/version-controlled. See *Known Issues* at the bottom of this document for a little more information.

### Repository Structure
In order to ensure that any changes to this repository do not break the projects that use them, it is expected that this repository will be used as a submodule of each project repository that is intended to use them.

* `<project repo>/digilent-vivado-scripts`: Submodule containing the scripts described by this document.
* `<project repo>/hw_handoff`: Used to contain the hardware handoff file.
* `<project repo>/proj`: Used to contain a checked-out Vivado project.
* `<project repo>/release`: Contains temporary files necessary to generate a release zip archive.
* `<project repo>/repo`: Contains local IP, IP submodules, and cached generated sources.
* `<project repo>/sdk`: Contains SDK projects, and is the workspace used with SDK.
  * `<repo>/sdk/.gitignore`: File describing which SDK files should be version controlled. Template generated by the checkin script.
* `<project repo>/src`: Contains source files for the Vivado Project.
  * `<project repo>/src/bd`: Contains a TCL script used to re-create a block design.
  * `<project repo>/src/constraints`: Contains XDC constraint files.
  * `<project repo>/src/hdl`: Contains Verilog and VHDL source files.
  * `<project repo>/src/ip`: Contains XCI files describing IP to be instantiated in non-IPI projects.
  * `<project repo>/src/others`: Contains all other required sources, such as memory initialization files.
* `<project repo>/.gitignore`: File describing which sources should be version controlled. Template is generated by the checkin process.
* `<project repo>/.gitmodules`: File describing submodules of the repository. Automatically maintained by the `git submodule` command.
* `<project repo>/project_info.tcl`: Script generated by first-time checkin used to save and re-apply project settings like board/part values. This can be modified after initial creation to manually configure settings that are not initially supported. **Note**: *This script should be deleted and recreated when porting a project from one board to another.*
* `<project repo>/README.md`: Markdown file describing the project and the process needed to use it, from downloading the release archive, to programming the FPGA.

------------
## Workflows

### 1. Cloning a Repo that uses this Submodule
In a console, first change the working directory (`cd`) to the location you wish to place the local version of the repo you will be cloning.

Clone the repository from github, using the `--recursive` flag, in order to pick up this and any other submodules installed in the repo.
    
  * `git clone --recursive <repo URL>`

**Important:** *Further example commands in this document assume that the working directory of the console you are running them in has been set to the cloned repo directory: `cd <repo>`*

If the repo was cloned non-recursively, the repo's submodules must be initialized from a console:

  * `git submodule init`

#### Vivado
Once the repo exists locally, the Vivado project can be checked out from source. To do this, use the following command:
    
  * `python3 ./digilent-vivado-scripts/git_vivado.py checkout`

Alternatively, the project can be checked out from within Vivado, by calling the following command in the TCL console:

  * `set argv ""; source ./digilent-vivado-scripts/digilent_vivado_checkout.tcl`

Both of these commands create a Vivado project within the repository's `proj` folder. In the case of the Python command, the project then needs to be opened from within Vivado.
#### SDK
1. To initialize the repo's SDK workspace (if it has one), first open SDK directly, choosing the repo's `sdk` folder as the workspace.

2. Use SDK's top menu bar to open the *File -> Import* dialog, select *General -> Existing Projects into Workspace*, and select all of the projects present in the repo's `sdk` folder.

3. To ensure that any changes made to the Vivado project are brought into the SDK workspace, the hardware platform project must be linked to the hardware handoff file. Right click on the `*_hw_platform_*` project and select *Change Hardware Specification*. Accept any warnings, then navigate to and select the repo's `hw_handoff` folder.

4. If errors occur at this stage, it may be necessary to *refresh* the projects in the workspace, *clean and rebuild* some of them, and/or *regenerate BSP sources*.


### 2. Creating a New Project
1. Create a folder on your computer to hold the project repository. Use the naming convention `<board>-<variant>-<project name>` (for example: `Zybo-Z7-20-DMA`). This folder will be referred to as the "local repo"

2. Create a repository on GitHub for your project with Digilent as the owner. Name it the same as the local repo folder. Do not have Github create a README, gitignore file, or license for you. This repository will be referred to as the "remote repo".

3. In a command line interface (git bash is recommended) cd into the local repo. Call the following set of commands, in order to initialize the repository, add these scripts to it, and set its remote.
    * `git init`
    * `git submodule add https://github.com/Digilent/digilent-vivado-scripts`
    * `git remote add origin <remote repo URL>`

4. While creating and developing your project using Vivado and Xilinx SDK, there are a few guidelines to follow:
    * When creating the project, make sure to place the Vivado project in a folder named `proj` in the local repo.
    * When exporting hardware to SDK, make sure to export to a folder named `hw_handoff` in the local repo. **Note**: *The checkin command, used in (5), below will also handle exporting the hardware handoff.*
    * When launching SDK, make sure to set the Exported Location as the hw_handoff folder, and the Workspace as a folder named `sdk` in the local repo.
    * If IPs or interfaces from [vivado-library](https://github.com/Digilent/vivado-library) are required, create a folder called `repo` in the local repo, and add vivado-library as a submodule within that folder.

5. Call the command below. This command can be called from anywhere in your filesystem, with relative paths changed as required. Missing required folders and files are automatically created, including gitignores. **Note:** *Invoking the script in this way uses all default arguments, which assume that the local repo directory structure is used. See* Creating a Repo from a Local Project, *below, for an alternate method.*
    * `python3 ./digilent-vivado-scripts/git_vivado.py checkin`

6. Create a README for the repo that specifies what the project is supposed to do and how to use a release archive for it. See *Using a Release Archive*, below, and the file `template_README.md` in digilent-vivado-scripts for more information.

7. Add, commit, and push your changes to the remote repo:

    * `git add .`
    * `git commit -m "Initial Commit"`
    * `git push origin master`

8. Create and upload a release ZIP to Github - see *Creating a Release Archive* below.

----
### 3. Creating a Repo from a Local Project
If your new project was not created following the directory structure described in *Creating a New Project*, above, this is the workflow to follow. This flow is a little more in depth. It assumes that a project (and SDK workspace) has already been created.

1. Create a repository on GitHub for your project with Digilent as the owner. Name it the same as the local repo folder. Do not have Github create a README, gitignore file, or license for you. This repository will be referred to as the "remote repo". Clone this repository to your computer - the folder where the repository is placed will be referred to as the "local repo".
    * `cd <intended parent directory of the local repo>`
    * `git clone --recursive <remote repo URL>`

2. In a command line interface (git bash is recommended) cd into the local repo. Call the following command in order add these scripts to the repository.
    * `git submodule add https://github.com/Digilent/digilent-vivado-scripts`

3. Use the checkin command of git_vivado.py to check the local project into the local repo, adding required folders, required files, and the projects sources:
    * `cd digilent-vivado-scripts`
    * `python3 git_vivado.py checkin -x <XPR file> -w <SDK workspace>`
    * `cd ..`

4. If any changes need to be made to the project during the checkout process, the project_info.tcl generated by the checkin command should be manually edited.

6. Create a README for the repo that specifies what the project is supposed to do and how to use a release archive for it. See *Using a Release Archive*, below, and the file `template_README.md` in digilent-vivado-scripts for more information.

5. Add, commit, and push your changes to the remote repo:
    * `git add .`
    * `git commit -m "Initial Commit"`
    * `git push origin master`

6. Create and upload a release ZIP to Github - see *Creating a Release Archive* below.


----
### 4. Retargeting an Existing Repo to use these Scripts
1. Clone (or pull) the Vivado project to be retargeted. Use its existing version control system to generate an XPR. If relevant, make sure to call `git submodule init` followed by `git submodule update` from a command line interface (git bash is recommended for Windows) from within the repo directory.

2. Open the project in Vivado and make any changes necessary (perhaps upgrading IP). When exporting to and launching SDK, make sure to use exported locations and workspaces that are not *Local to Project*.

3. Clone the project repository again in a different location. Remove all files from this directory.

4. In a command line interface (git bash) cd into the clean repository directory. Call the following command: 
    * `git submodule add https://github.com/Digilent/digilent-vivado-scripts`

5. Use the checkin command of git_vivado.py to check the project into the clean local repo, adding required folders, required files, and the projects sources:
    * `python3 ./digilent-vivado-scripts/git_vivado.py checkin -x <XPR file> -w <SDK workspace>`

6. If any changes need to be made to the project during the checkout process, the project_info.tcl generated by the checkin command should be manually edited.

7. If required, copy all files from the project's SDK workspace into the repo's `sdk` folder.

8. Create a README for the repo that specifies what the project is supposed to do and how to use a release archive for it. See *Using a Release Archive*, below, and the file `template_README.md` in this submodule for more information.

9. Add, commit, and push your changes to the remote repo:
    * `git add .`
    * `git commit -m "Initial Commit"`
    * `git push origin master`

10. Create and upload a release ZIP to Github - see *Creating a Release Archive* below.

----
### 5. Making Changes to a Project that uses this Submodule
1. Clone the Vivado project to be changed. **Note**: *Pull the repo instead, if you already have a local instance of the project.*
    * `git clone --recursive <remote repo URL>`

2. In a command line interface (git bash is recommended for Windows) cd into the local project.

**NOTE**: Steps 3, 4, and 5 are only required if changes to the Vivado project are required.

3. Call the command below. This command can be called from anywhere in your filesystem, with the relative path to git_vivado. This will also create a gitignore file for the repository. Default arguments will create the XPR at `<project repo>/proj/<project name>.xpr`.
    * `python3 <path to digilent-vivado-scripts>/git_vivado.py checkout`

4. Open the project in Vivado and make any changes necessary (perhaps upgrading IP or fixing a bug). When exporting to and launching SDK, make sure to use the local repo's `hw_handoff` folder for the exported location and `sdk` folder for the workspaces.

5. Call the command below. This command can be called from anywhere in your filesystem, with the relative path to git_vivado changed as required. Default arguments are fine, as they assume the use of the `proj` and `sdk` folders. Add the `-no_hdf` flag if you do not wish to overwrite the hardware handoff file.
    * `python3 <path to digilent-vivado-scripts>/git_vivado.py checkin`

6. Open Xilinx SDK, using the local repo's `sdk` folder as it's workspace. 

    **Important**: *If this is your first time cloning this repo, and there are projects in the sdk folder, you will need to initialize the workspace by launching SDK directly, rather than through Vivado. Launching from Vivado may create a duplicate hardware platform.*

    If you already had an instance of the project on your system, you may only need to open SDK with the local repo's `sdk` folder as the workspace.

    If the hardware handoff file has changed since the workspace was first initialized, you may need to right click on the hw_platform project and select *Change Hardware Specification* in order to point it to the hw_handoff folder's .hdf file.

    Projects that have been added to the repository since it was initialized (all projects, if the repo was just cloned) must be imported into the workspace, by selecting *File -> Import*, then navigating the dialog to select *Existing Projects into Workspace* from the local repo's `sdk` folder.

7. Make sure to update the repo's README as required.

8. Add, commit, and push your changes.
    * `git add .`
    * `git commit -m "Initial Commit"`
    * `git push origin master`

9. Create and upload a release ZIP to GitHub - see *Creating a Release Archive* below.

----
### 6. Creating a Release Archive
1. If a README has not been created for the repo, first create one.

2. Open the repo's Vivado project, and make sure that the bitstream is up to date and that hardware has been exported to the hw_handoff folder (if applicable).

3. Open the repo's SDK workspace, and make sure that the project builds fully and is functional.

4. If the Vivado project is located in the local repo's proj folder, and the SDK workspace is located in the local repo's sdk folder, the command below can be used with all default arguments to create a release zip archive. By default the output ZIP file will be placed in a release_# folder of the local repo (which is ignored by the version control system).
    *  `python3 <path to digilent-vivado-scripts>/git_vivado.py release`

**NOTE** *The Python script is required to stitch together files released by Vivado and SDK. It calls into digilent_vivado_release.tcl and digilent_sdk_release.tcl. When sourced in Vivado's TCL console (vivado_release), or SDK's XSCT console (sdk_release), these TCL scripts can still be used to create the individual components of a release.*

5. Take the ZIP archive output by the script, and add a minor version number to its name, such that the name follows the pattern: `<project name>-<vivado version number>-<minor version number>.zip` (for example, `Zybo-Z7-20-DMA-2018.2-3.zip`).

6. Draft a new release on Github and upload the ZIP to it. Give the release a descriptive title including the name of the project and the tool version number it supports. Use the format `v<vivado version number>-<minor version number>` (for example, `v2018.2-3`) for the version tag. Add text specifying the name of the ZIP that the user must download to the release's description field.

----
### 7. Using a Release Archive
1. Download and extract the most recent release archive from the repository's releases page.
2. Open the project in the version of Vivado specified by the README, by using the *Open Project* dialog and selecting the project's .xpr file.
#### Vivado Only
3. The Vivado project will already have a bitstream generated, open the Hardware Manager, connect to your board, and program it.
#### Vivado + Xilinx SDK
3. Launch Xilinx SDK, selecting the sdk_workspace folder of the extracted release for the SDK workspace.
4. Use the File->Import dialog to import all projects from the sdk_workspace folder into the workspace.
5. Right click on the application project's src folder and select *Import*. Import all files from `<extracted location>/sdk_appsrc`, overwriting anything that already exists.
6. Use the Xilinx->Program dialog and Run option in the application project's right-click menu to program the board and run the application on it.
7. If changes are later made to the Vivado design, the SDK hardware platform must be changed to reflect the Vivado changes: After generating a bitstream, use Vivado's *File->Export->Export Hardware* dialog to create a handoff file. Then, in SDK, right click on the hardware platform project and select *Change Hardware Specification* to point the hardware platform to the new handoff file.

----
### Appendix: Using the TCL Scripts from the TCL Console

Each TCL script in this repository can be sourced from the TCL (or XSCT) console in the appropriate tool. `digilent_vivado_*` scripts can only be sourced from Vivado, while `digilent_sdk_*` scripts can only be sourced from SDK's XSCT console (Xilinx->XSCT in the SDK GUI). Arguments are passed to these scripts through the use of the `argv` variable. Care should be taken to ensure that the wrong arguments are not passed to these scripts.

Sourcing a script and passing all default arguments can be accomplished in the following way:
* `set argv ""`
* `source <path to digilent-vivado-scripts>/<script name>.tcl`

An example of  passing non-default arguments (checking in a local "My_Project" to a local "My_Repo"):
* `set argv "-r C:/My_Repo -x C:/My_Project/My_Project.xpr -w C:/My_Project/My_Project.sdk"`
* `source digilent_vivado_checkin.tcl`

----
## Known Issues
* Each developer may need their own version of the configuration file, config.ini, for each project they are working on. The configuration file should be moved to somewhere outside of the repo submodule to accomodate this, in a predictable location on Linux and Windows. The Python script will need to be updated to accomodate this, a location and less generic name will need to be chosen for the configuration file.
* The *Archive Project* functionality of Vivado may include local SDK sources in the release archive. This should be avoided so that users have a clean workspace to Export and Launch SDK into. The current process requires that the project's SDK workspace is created external to the Vivado project.
* There is some danger that modifications to Digilent's board files may break existing projects, it may be worth considering adding the vivado-boards repository as a submodule to project repositories.
* Releases do not contain a hardware handoff, requiring that the user open Xilinx SDK directly, rather than through Vivado.
