# digilent-vivado-scripts

This is a repo with scripts for creating, maintaining and releasing git repositories
that contain minimally version-controlled Vivado projects. It contains solutions for the
check in/out workflow, plus a clean/build helper that can also export the `.xsa` hardware
handoff and a release archive. The scripts handle all the necessary tasks to ensure a
smooth workflow for development of the `proj` Vivado project.

**Note #1:**
*To add this repository to a parent repository as a submodule, first open a terminal*
*with access to `git`:*

`git submodule add https://github.com/Digilent/digilent-vivado-scripts`

**Note #2:**
*The checkout/checkin scripts expect the parent repository to follow the layout below.*
*Missing folders and files are created by `checkin`, see **Repository Structure**.*

* `src\` holds the version-controlled sources: `bd`, `constraints`, `hdl`, `ip`,
  `other` and optionally `sim`.
* `repo\` holds local IP and IP submodules.
* `proj\` holds the generated Vivado project (not version-controlled).
* `hw_handoff\` holds the exported `.xsa` hardware platform.

**Note #3:**
*Python 3.6.3 (or newer) is required for the Python front-ends. No additional Python*
*modules are needed. Each script can also be sourced from the Vivado Tcl console.*

**Special Note:**
*`git_vivado.py` writes `vivado.jou`/`vivado.log` to the current working directory.*
*`clean_build.py` redirects them to `proj\logs\` (`proj\logs\<variant>\` for parallel*
*variant builds).*

----

## Quick Checkout Guide

1. Clone the repository together with its submodules:

   `git clone --recursive <repo URL>`

   If it was cloned non-recursively, initialize the submodules:

   `git submodule update --init [--recursive]`

2. Some demo repositories use one branch per demo. After checking out a branch, update
   the submodules again (same command as above).

3. If a project was checked out before, run `clean_build.py --clean` or delete the
   `proj` folder first.

4. Create the project from a terminal, using the Python front-end:

   `python <path-to-scripts-repo>\git_vivado.py checkout -v <version>`

   The project is created in `<repo>\proj\<repo name>.xpr`.

5. Or from the Vivado Tcl console, which opens the project right away:

   `set argv ""; source <path-to-scripts-repo>/checkout.tcl`

6. Open the project in Vivado (not needed for step 5). All sources are available, a
   bitstream can be generated and an `.xsa` can be exported for Vitis.

**Note:**
*The current working directory is irrelevant for the Tcl scripts when `-r` and `-x` are*
*omitted: the defaults are derived from the location of the scripts.*

----

## Quick Checkin Guide

**Important:** *`checkin` updates the files in `src\` and removes the ones no longer in*
*the project. `project_info.tcl`, `post_build.tcl` and `.gitignore` are created only when*
*missing; delete one to have it recreated. Projects with more than one block design are*
*not supported and stop with an error.*

**Note:**
*This section assumes that you have already created a Vivado project, either with*
*`checkout` or by hand.*

1. Build the project in Vivado. Do NOT export the hardware yet.

2. Close or keep the project open, both work. Run the check in:

   `python <path-to-scripts-repo>\git_vivado.py checkin -x <xpr path>`

   Or from the Vivado Tcl console:

   `set argv "-x <xpr path>"; source <path-to-scripts-repo>/checkin.tcl`

3. Use `git status` to see what changed under `src\`, then commit logically
   (one commit per concern).

4. Export the hardware platform to `hw_handoff\` and commit it separately, so it is
   easy to tell which `.xsa` belongs to which version (see **Quick Build Guide**).

----

## Quick Build Guide

`clean_build.py` combines cleaning `proj\`, creating and/or building the project,
and optionally exporting the `.xsa` and a release archive, in one command.
It does not change any `git_vivado.py` behavior.

1. Close Vivado if it has the project open.

2. Run the helper. It finds the Vivado install on its own, see **Vivado Auto-Discovery**:

   `python <path-to-scripts-repo>\clean_build.py -v <version> --clean --build`

3. Typical variations:

   `python <path-to-scripts-repo>\clean_build.py -v <version> --clean --checkout` (create only)

   `python <path-to-scripts-repo>\clean_build.py -v <version> --build --xsa` (build, then export)

   `python <path-to-scripts-repo>\clean_build.py -v <version> --archive` (release ZIP only)

4. Output:

   * `<repo>\proj\` holds the project.
   * `<repo>\hw_handoff\<top>.xsa` holds the hardware platform (`--xsa`).
   * `<repo>\release\<project>.xpr.zip` holds the archive (`--archive`).
   * `<repo>\proj\logs\<variant>\<step>.log` holds the full logs of each variant.

**Note:**
*All flags are independent and can be combined; at least one is required.*
*`--build` takes precedence over `--checkout`.*

### Building Variants

A project's own BD script can read a global Tcl variable to switch build-time options
(for example a hardware option fitted on the board). `clean_build.py` builds one
independent project per value:

`python <path-to-scripts-repo>\clean_build.py -v <version> --clean --build --xsa -j 0 --variant-tclvar <NAME> --variant-values <a>,<b>`

* Each variant gets its own subdirectory: `proj\<value>\<project>.xpr`.
* Each variant gets its own IP cache (`proj\cache-<value>`), logs, archive scratch and
  per-user Xilinx directory (`proj\user-<value>`, with your licenses copied in), so
  parallel builds cannot corrupt each other. Vivado rewrites its shared `tclapp` manifest
  on every start, and concurrent starts break runs with `tclapp::load_apps failed`.
* A run that still fails that way is repeated once; real design errors are not retried.
* `-j 0` runs one job per variant. A full build needs roughly 8 GB of RAM per job.
* The scripts have no knowledge of what the variable means; it is up to the BD script.

### Vivado Auto-Discovery

Since Vivado 2025.1 the default install root is `AMDDesignTools` instead of `Xilinx`
and the layout changed from `<root>/Vivado/<version>/bin` to `<root>/<version>/Vivado/bin`.
`clean_build.py` resolves the Vivado command in this order:

1. The install root saved in `config.ini` (or given with `-i`), trying both layouts.
2. Auto-scan of all drive letters on Windows, or `/opt`, `/tools`, `~` on Linux, for
   both root names and both layouts.

The version and install root that were found are saved to `<repo>\config.ini`, so later
runs need no flags. The same applies to `git_vivado.py`. Without `-v` or a saved version,
the newest installed version is used.

----

## Command Reference (copy/paste, replace placeholders as needed)

**Note:**
*Replace `<version>` with the installed Vivado version (e.g. `2025.2`), `<xpr path>`*
*with the project file and `<path-to-scripts-repo>` with the absolute or relative path*
*to this repository (the scripts submodule). Paths passed as arguments must be absolute*
*or relative to the current working directory.*

**`git_vivado.py` global flag** (goes before the subcommand, e.g. `git_vivado.py -f checkout`):

* `-f`: skip confirmation prompts.

**`git_vivado.py checkout` flags** (combinable):

| Flag | Description | Default |
|------|-------------|---------|
| `-r <repo>` | Repository directory | `<scripts>/..` |
| `-x <xpr>` | Project file to create | `<repo>/proj/<repo name>.xpr` |
| `-v <version>` | Vivado version, saved to `config.ini` | `config.ini`, else newest installed |
| `-i <install root>` | Vivado install root, saved to `config.ini` | `config.ini` |
| `-b` | Build the project after checkout; the `post_build.tcl` runs after it | off |

**`checkout.tcl` flags** (set in `argv`, combinable):

| Flag | Description | Default |
|------|-------------|---------|
| `-r <repo>` | Repository directory | `<scripts>/..` |
| `-x <xpr>` | Project file to create | `<repo>/proj/<repo name>.xpr` |
| `-v <version>` | Vivado version | `version -short` |
| `-b` | Build after checkout | off |
| `-no-block` | With `-b`, return as soon as the build starts | off |
| `-ip-cache <dir>` | IP output repository, one per project for parallel builds | `<repo>/proj/cache` |
| `-D <NAME> <VALUE>` | Set a global Tcl variable for the BD script (repeatable) | none |

**Note:**
*`-D` takes NAME and VALUE as two separate tokens, not `NAME=VALUE`, because*
*`vivado.bat` splits unquoted arguments on `=`.*

**`git_vivado.py checkin` / `checkin.tcl` flags** (combinable):

| Flag | Description | Default |
|------|-------------|---------|
| `-r <repo>` | Repository directory | `<scripts>/..` |
| `-x <xpr>` | Project file to check in | `<repo>/proj/*.xpr` |
| `-v <version>` | Vivado version (Python only) | `config.ini`, else newest installed |
| `-i <install root>` | Vivado install root (Python only) | `config.ini` |

**`clean_build.py` flags** (combinable, at least one action required):

| Flag | Description |
|------|-------------|
| `-r <repo>`, `-x <xpr>`, `-v <version>`, `-i <install root>` | Same as above |
| `-f` | Skip confirmation prompts |
| `--clean` | Delete the contents of `proj\` (except `.keep`) first |
| `--checkout` | (Re)create the project, no build |
| `--build` | Create (if needed) and build: synth, impl, write_bitstream |
| `--xsa` | Export the fixed `.xsa` with bitstream to `hw_handoff\` |
| `--archive` | Create the release ZIP in `release\` |
| `--variant-tclvar <NAME>` | Tcl variable set once per `--variant-values` entry |
| `--variant-values <a,b>` | Comma-separated values, one project each |
| `-j`, `--jobs <N>` | Concurrent variants, `0` is one per variant (default 1) |
| `--verbose` | With `-j` above 1, echo every output line |
| `--fix-tclapp` | Delete a truncated per-user Vivado `tclapp\manifest.tcl` |

**`export_xsa.tcl` and `archive_project.tcl` flags** (set in `argv`):

| Flag | Script | Description |
|------|--------|-------------|
| `-x <xpr>` | both | Project file (required) |
| `-o <name>` | both | Output name, avoids clashes between variants |
| `-r <repo>` | both | Repo for `hw_handoff\`/`release\`, default is the xpr grandparent |
| `-t <dir>` | archive | Scratch directory, default `<repo>/temp` |

**Windows / Linux (`python` / `python3`)**:

```bat
:: create the project only
python <path-to-scripts-repo>\git_vivado.py checkout

:: create and build the project
python <path-to-scripts-repo>\git_vivado.py checkout -b -v <version>

:: back up the current project sources into src\
python <path-to-scripts-repo>\git_vivado.py checkin -x <xpr path>

:: wipe proj\ and rebuild from scratch
python <path-to-scripts-repo>\clean_build.py -v <version> --clean --build

:: full flow: rebuild, export the xsa and create the release archive
python <path-to-scripts-repo>\clean_build.py -v <version> --clean --build --xsa --archive
```

**Vivado Tcl console**:

```tcl
# create the project
set argv ""; source <path-to-scripts-repo>/checkout.tcl

# create and build, with a build-time option for the BD script
set argv "-b -D <NAME> <VALUE>"; source <path-to-scripts-repo>/checkout.tcl

# check in the opened project
set argv "-x <xpr path>"; source <path-to-scripts-repo>/checkin.tcl

# export the xsa of a built project
set argv "-x <xpr path> -o <name>"; source <path-to-scripts-repo>/export_xsa.tcl
```

----

## Repository Structure

**Note:**
*Using the scripts as a submodule keeps changes here from breaking the projects.*

| Path | Description |
|------|-------------|
| `<project repo>/<scripts>` | This submodule |
| `<project repo>/hw_handoff` | Exported hardware handoff (`.xsa`) |
| `<project repo>/proj` | Checked-out Vivado project and generated sources |
| `<project repo>/release` | Release ZIP archives |
| `<project repo>/temp` | Scratch space for the archive |
| `<project repo>/repo` | Local IP and IP submodules |
| `<project repo>/src/bd` | Tcl script that re-creates the block design |
| `<project repo>/src/constraints` | XDC constraint files |
| `<project repo>/src/hdl` | Verilog, VHDL and SystemVerilog sources |
| `<project repo>/src/ip` | XCI files for non-IPI projects |
| `<project repo>/src/other` | Other sources, e.g. memory initialization files |
| `<project repo>/src/sim` | One folder per simulation set |
| `<project repo>/.gitignore` | Template generated by the first checkin |
| `<project repo>/project_info.tcl` | Board, part and run settings, see below |
| `<project repo>/post_build.tcl` | Runs after a blocking `-b` build, see below |
| `<project repo>/README.md` | How to use the project and its release archive |

* `project_info.tcl` is generated by the first checkin. Edit it to configure settings
  that are not captured, and delete it to recreate it when porting to another board.
* `post_build.tcl` is a stub generated by the first checkin. Customize it to export
  the bitstream, the `.xsa` or a release archive (examples are in the template).

### Configuration File

`<project repo>\config.ini` holds the Vivado install root and version of this machine.
It is written by `git_vivado.py` and `clean_build.py` from `-v` and `-i`, is not
version-controlled, and can be deleted at any time to be detected again.

```ini
[Vivado]
installpath = <drive>/AMDDesignTools
version = <version>
```

----

## Workflows

### 1. Creating a New Project

1. Create a folder named `<board>-<variant>-<project name>`
   (e.g. `Zybo-Z7-20-DMA`) and a GitHub repository with the same name.
   Do not let GitHub create a README, gitignore or license.

2. Initialize the repo, add the scripts and set the remote:

   * `git init`
   * `git submodule add https://github.com/Digilent/digilent-vivado-scripts`
   * `git remote add origin <remote repo URL>`

3. While developing the project in Vivado:

   * Place the Vivado project in the `proj` folder of the repo.
   * Export the hardware to the `hw_handoff` folder of the repo.
   * Add IP libraries, e.g. [vivado-library](https://github.com/Digilent/vivado-library),
     as submodules inside the `repo` folder.

4. Check in the project. Missing folders and files, including gitignores, are created:

   `python <path-to-scripts-repo>\git_vivado.py checkin`

5. Write a README describing what the project does and how to use a release archive.

6. Commit and push, then create the release archive (see workflow 4).

### 2. Creating a Repo from a Local Project

Use this when the project was not created with the layout of workflow 1.

1. Create the GitHub repository (same rules as above) and clone it recursively.

2. Add the scripts: `git submodule add https://github.com/Digilent/digilent-vivado-scripts`

3. Check the local project in, creating the folders, files and sources:

   `python <path-to-scripts-repo>\git_vivado.py checkin -x <xpr path>`

4. Edit the generated `project_info.tcl` if the checkout needs different settings.

5. Write the README, then commit and push.

### 3. Making Changes to a Project

1. Clone the project recursively, or pull it if a local copy exists.

2. Only if the Vivado project must change: run `checkout`, change and build the
   project in Vivado (do NOT export hardware yet), then run `checkin`.

3. Update the README, then commit and push with an informative message.

4. Export the hardware platform to `hw_handoff\` and commit it separately,
   e.g. with the message "Export hardware".

5. Create the release archive (workflow 4).

### 4. Creating a Release Archive

1. Make sure the repo has a README.

2. Create the archive with `clean_build.py --archive`, or with Vivado's
   File > Project > Archive. It packages all sources, including IP and board files.

3. Name the ZIP `<project name>-<vivado version>-<minor version>.zip`
   (e.g. `Zybo-Z7-20-DMA-2018.2-3.zip`).

4. Draft a GitHub release:

   * Tag: `v<vivado version>-<minor version>` (e.g. `v2018.2-3`).
   * Title: project name and the supported tool version.
   * Description: the name of the ZIP the user must download.

5. If the project has a software component, release it as well.

### 5. Using Simulations

`checkout` supports basic checkout of simulation sources. Checkin is manual.

* Each simulation (sources and testbench) gets its own folder in `<repo>/src/sim`.
* Files in it (Verilog, VHDL, `.wcfg`) go only into the simulation fileset of that folder.
* All design sources are available to every simulation set.
* The top module is the file with the suffix `_tb` (e.g. `my_simulation_tb.v`).
  Only one file per simulation should have it.

To run a simulation:

1. In the Sources tab, right-click the simulation set (e.g. `sim_1`), "Make Active".
2. In the Flow Navigator select "Run Simulation > Run Behavioral Simulation".
3. To run another one, make it active and run again. "Relaunch Simulation" reruns it.
