# Digilent Vivado Scripts

## Introduction
This repository contains a set of scripts for creating, maintaining, and releasing git repositories containing minimally version-controlled Vivado projects. A Python 3.6.3 (or newer) installation is required to use the Python frontend for these scripts. As of time of writing, no additional Python modules are depended on.

----------------
## Quick Guide

This guide covers only what is required to gain access to and build demo project sources. For more in-depth details on these steps, and for information on how to push changes to a demo repository or build a release, see the **Workflows** section of this document, below.

### Prerequisites
- You must have the URL for a demo repository that uses digilent-vivado-scripts as a submodule. 
  
    For the purposes of this guide, any time that the text `<demo>` appears, you should replace it with the name of your chosen demo, as it appears at the end of the URL. For example, for the [Zybo Z7-20 HDMI demo](https://github.com/Digilent/Zybo-Z7-20-HDMI), `<demo>` should be replaced with `Zybo-Z7-20-HDMI`.
- Make sure that [Git](https://git-scm.com/) and a console application that can use it are installed on your computer. Most Linux systems will already have git installed. Windows users are recommended to use the Git Bash shell available through https://gitforwindows.org.
- Make sure you have the version of Vivado targeted by your chosen demo repository installed on your computer. The README for your chosen demo will describe which version of these tools it can be used with. Installation instructions can be found in the [Installing Vivado, Xilinx SDK, and Digilent Board Files](https://reference.digilentinc.com/vivado/installing-vivado/start) guide on the Digilent Wiki. FIXME update link
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

    `set argv ""; source <path>/<demo>/scripts/checkout.tcl`
1. At this point you now have access to the Vivado Project and all of its sources. The project can be viewed, changes can be made, a bitstream can be generated, and Xilinx shell architecture file (XSA) can be generated for handoff to Vitis.
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
This subcommand calls into checkout.tcl in order to create a Vivado project, in the form of an XPR file, using the sources and scripts contained in the project repository.
#### Optional Arguments
1. `-r <repo>`: Path to the repository directory. Default: `<digilent-vivado-scripts>/..`
1. `-x <xpr>`: Path to the project .xpr file the repo is to be checked out into. Default: `<repo>/proj/<repo name>.xpr`
1. `-v <version>`: Vivado version number. Default contained in config.ini. (Python only)
1. `-b`: Build project after its checked out. Depending on post_build script, may also export files to hw_handoff and/or release directories.
1. `-no-block`: If -b is specified, exit the script as soon as the build is started. Not available in the Python script.
**Note**: *All paths passed as arguments must either be absolute or relative to the current working directory.*
#### Example Usage
##### Python:
> `python3 git_vivado.py checkout -r D:/Github/Zybo-Z7/hw`

##### TCL:
> `set argv "-r D:/Github/Zybo-Z7/hw"`

> `source checkout.tcl`

-----------
### Checkin
#### Description
This subcommand calls into checkin.tcl in order to collect sources and generate needed scripts from a Vivado project into the repository structure described below. Files required for checkout *that are not already present* in the repository (such as project_info.tcl and gitignores), are automatically created. These files are not overwritten if they already exist.
#### Optional Arguments
1. `-r <repo>`: Path to the repository directory. Default: `<digilent-vivado-scripts>/..`
1. `-x <xpr>`: Path to the project .xpr file to be processed for checkin. Default: `<repo>/proj/*.xpr`
1. `-v <version>`: Vivado version number. Default contained in config.ini. (Python only)

**Note**: *All paths passed as arguments must either be absolute or relative to the current working directory.*
#### Example Usage
##### Python:
> `python3 git_vivado.py checkin -r D:/Github/Zybo-Z7/hw`

##### TCL:
> `set argv "-r D:/Github/Zybo-Z7/hw"`

> `source checkin.tcl`

------------------------------------
## Other Files and Overall Structure
### Configuration File
The digilent-vivado-scripts repository contains a file named `config.ini`. This file contains several values used by the Python frontend to determine what the default arguments for the different subcommands should be. It has not yet been decided how this file should be managed/version-controlled. See *Known Issues* at the bottom of this document for a little more information.

### Repository Structure
In order to ensure that any changes to this repository do not break the projects that use them, it is expected that this repository will be used as a submodule of each project repository that is intended to use them.

* `<project repo>/scripts`: Submodule containing the scripts described by this document.
* `<project repo>/hw_handoff`: Used to contain the hardware handoff file.
* `<project repo>/proj`: Used to contain a checked-out Vivado project, and cached generated sources.
* `<project repo>/release`: Contains temporary files necessary to generate a release zip archive.
* `<project repo>/repo`: Contains local IP, IP submodules.
* `<project repo>/src`: Contains source files for the Vivado Project.
  * `<project repo>/src/bd`: Contains a TCL script used to re-create a block design.
  * `<project repo>/src/constraints`: Contains XDC constraint files.
  * `<project repo>/src/hdl`: Contains Verilog and VHDL source files.
  * `<project repo>/src/ip`: Contains XCI files describing IP to be instantiated in non-IPI projects.
  * `<project repo>/src/others`: Contains all other required sources, such as memory initialization files.
* `<project repo>/.gitignore`: File describing which sources should be version controlled. Template is generated by the checkin process.
* `<project repo>/.gitmodules`: File describing submodules of the repository. Automatically maintained by the `git submodule` command.
* `<project repo>/project_info.tcl`: Script generated by first-time checkin used to save and re-apply project settings like board/part values. This can be modified after initial creation to manually configure settings that are not initially supported. **Note**: *This script should be deleted and recreated when porting a project from one board to another.*
* `<project repo>/post_build.tcl`: Script generated by first-time checkin that is run after checkout builds. Intended to be used to export handoff and release files.
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

  * `set argv ""; source ./digilent-vivado-scripts/checkout.tcl`

Both of these commands create a Vivado project within the repository's `proj` folder. In the case of the Python command, the project then needs to be opened from within Vivado.

### 2. Creating a New Project
1. Create a folder on your computer to hold the project repository. Use the naming convention `<board>-<variant>-<project name>` (for example: `Zybo-Z7-20-DMA`). This folder will be referred to as the "local repo"

2. Create a repository on GitHub for your project with Digilent as the owner. Name it the same as the local repo folder. Do not have Github create a README, gitignore file, or license for you. This repository will be referred to as the "remote repo".

3. In a command line interface (git bash is recommended) cd into the local repo. Call the following set of commands, in order to initialize the repository, add these scripts to it, and set its remote.
    * `git init`
    * `git submodule add https://github.com/Digilent/digilent-vivado-scripts`
    * `git remote add origin <remote repo URL>`

4. While creating and developing your project using Vivado, there are a few guidelines to follow:
    * When creating the project, make sure to place the Vivado project in a folder named `proj` in the local repo.
    * When exporting hardware, make sure to export to the folder named `hw_handoff` in the local repo.
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
If your new project was not created following the directory structure described in *Creating a New Project*, above, this is the workflow to follow. This flow is a little more in depth. It assumes that a project has already been created.

1. Create a repository on GitHub for your project with Digilent as the owner. Name it the same as the local repo folder. Do not have Github create a README, gitignore file, or license for you. This repository will be referred to as the "remote repo". Clone this repository to your computer - the folder where the repository is placed will be referred to as the "local repo".
    * `cd <intended parent directory of the local repo>`
    * `git clone --recursive <remote repo URL>`

2. In a command line interface (git bash is recommended) cd into the local repo. Call the following command in order add these scripts to the repository.
    * `git submodule add https://github.com/Digilent/digilent-vivado-scripts`

3. Use the checkin command of git_vivado.py to check the local project into the local repo, adding required folders, required files, and the projects sources:
    * `cd digilent-vivado-scripts`
    * `python3 git_vivado.py checkin -x <XPR file>`
    * `cd ..`

4. If any changes need to be made to the project during the checkout process, the project_info.tcl generated by the checkin command should be manually edited.

5. Create a README for the repo that specifies what the project is supposed to do and how to use a release archive for it. See *Using a Release Archive*, below, and the file `template_README.md` in digilent-vivado-scripts for more information.

6. Add, commit, and push your changes to the remote repo:
    * `git add .`
    * `git commit -m "Initial Commit"`
    * `git push origin master`

7. Create and upload a release ZIP to Github - see *Creating a Release Archive* below.


----
### 4. Making Changes to a Project that uses this Submodule
1. Clone the Vivado project to be changed. **Note**: *Pull the repo instead, if you already have a local instance of the project.*
    * `git clone --recursive <remote repo URL>`

2. In a command line interface (git bash is recommended for Windows) cd into the local project.

**NOTE**: Steps 3, 4, and 5 are only required if changes to the Vivado project are required.

3. Call the command below. This command can be called from anywhere in your filesystem, with the relative path to git_vivado. This will also create a gitignore file for the repository. Default arguments will create the XPR at `<project repo>/proj/<project name>.xpr`.
    * `python3 <path to digilent-vivado-scripts>/git_vivado.py checkout`

4. Open the project in Vivado and make any changes necessary (perhaps upgrading IP or fixing a bug). Build the project. Do NOT export hardware yet.

5. Call the command below. This command can be called from anywhere in your filesystem, with the relative path to git_vivado changed as required. Default arguments are fine, as they assume the use of the `proj` folder.
    * `python3 <path to digilent-vivado-scripts>/git_vivado.py checkin`

7. Make sure to update the repo's README as required.

8. Add, commit, and push your changes.
    * `git add .`
    * `git commit -m "Write an informative message here"`
    * `git push origin master`

9. Export the hardware platform from Vivado into the local repo's `hw_handoff` folder. Commit and push it with the commit message "Export Hardware".

10. Create and upload a release ZIP to GitHub - see *Creating a Release Archive* below.

----
### 5. Creating a Release Archive
1. If a README has not been created for the repo, first create one.

2. Use Vivado's File > Project > Archive menu option to create a release ZIP file for the project. This will package all sources depended on by the project, including IP and board files into a single ZIP, allowing it to be used on a system that does not have these sources previously installed.

3. Take the new ZIP archive, and add a minor version number to its name, such that the name follows the pattern: `<project name>-<vivado version number>-<minor version number>.zip` (for example, `Zybo-Z7-20-DMA-2018.2-3.zip`).

4. Draft a new release on Github and upload the ZIP to it. Give the release a descriptive title including the name of the project and the tool version number it supports. Use the format `v<vivado version number>-<minor version number>` (for example, `v2018.2-3`) for the version tag. Add text specifying the name of the ZIP that the user must download to the release's description field.

5. If the project has a software component, review appropriate documentation to release it as well.

----
## Known Issues
* Each developer may need their own version of the configuration file, config.ini, for each project they are working on. The configuration file should be moved to somewhere outside of the repo submodule to accomodate this, in a predictable location on Linux and Windows. The Python script will need to be updated to accomodate this, a location and less generic name will need to be chosen for the configuration file. Additional note, requiring that a single Xilinx install directory containing all versions to be used be included in the path may be a better solution.
* There is some danger that modifications to Digilent's board files may break existing projects, it may be worth considering adding the vivado-boards repository as a submodule to project repositories.
