# PYTHON 3.X.X REQUIRED!!!
"""
clean_build.py

Cleans the Vivado 'proj' working directory and, optionally, (re)creates the
project from the repo/ sources and/or builds it (synth -> impl -> bitstream).

This script is additive: it does not change or remove any existing
functionality in git_vivado.py (checkin/checkout/release keep working as
before). It reuses git_vivado.do_checkout() so the checkout.tcl code path
stays identical.

Vivado install auto-discovery
------------------------------
Starting with Vivado 2025.1, AMD renamed the default installation root from
"Xilinx" to "AMDDesignTools". Additionally, in some versions the on-disk
layout itself changed from "<root>/Vivado/<version>/bin" (older) to
"<root>/<version>/Vivado/bin" (2025.1+). The tools may also be installed on
any drive/partition letter, not just C:. Resolution order:
  1. config.ini's VivadoInstallPath + <version> (existing/unchanged behavior),
     tried against both known layouts.
  2. Auto-scan: on Windows, every available drive letter is checked for both
     root directory names ("AMDDesignTools", "Xilinx") and both layouts;
     on Linux, a handful of common install locations are checked the same way.
"""

import argparse
import ctypes
import os
import platform
import shutil
import string
import sys

import git_vivado

# Root directory names Vivado has been installed under, in search priority order.
# Vivado 2025.1+ uses "AMDDesignTools"; earlier versions use "Xilinx".
VIVADO_ROOT_DIR_NAMES = ['AMDDesignTools', 'Xilinx']


def list_windows_drives():
    """Returns available drive roots on Windows, e.g. ['C:\\\\', 'D:\\\\', 'E:\\\\']."""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drives.append('%s:\\' % letter)
    return drives


def vivado_layout_candidates(root_base, version, exe_name):
    """
    Returns both known on-disk install layouts under an install root, e.g. for
    root_base="E:\\AMDDesignTools" and version="2025.2":
      - E:\\AMDDesignTools\\Vivado\\2025.2\\bin\\vivado.bat  (older layout)
      - E:\\AMDDesignTools\\2025.2\\Vivado\\bin\\vivado.bat  (2025.1+ layout)
    """
    return [
        os.path.join(root_base, 'Vivado', version, 'bin', exe_name),
        os.path.join(root_base, version, 'Vivado', 'bin', exe_name),
    ]


def find_vivado_cmd(version, configured_install_path=None):
    """
    Locates the vivado executable for `version`.

    Search order:
      1. Both known layouts under configured_install_path (config.ini,
         unchanged behavior) and, in case config.ini already points at a
         ".../Vivado" style path (older convention), under its parent too.
      2. Both known layouts under "<root>/<root_dir_name>" for every root
         name in VIVADO_ROOT_DIR_NAMES, where <root> is every drive letter
         on Windows, or a common install base on Linux.

    Returns the path to the vivado command if found, otherwise None.
    """
    exe_name = 'vivado.bat' if platform.system() == 'Windows' else 'vivado'
    candidates = []

    if configured_install_path:
        configured_install_path = os.path.abspath(configured_install_path)
        candidates += vivado_layout_candidates(configured_install_path, version, exe_name)
        candidates += vivado_layout_candidates(os.path.dirname(configured_install_path), version, exe_name)

    if platform.system() == 'Windows':
        root_bases = [os.path.join(drive, root_dir_name)
                      for drive in list_windows_drives()
                      for root_dir_name in VIVADO_ROOT_DIR_NAMES]
    else:
        root_bases = [os.path.join(base, root_dir_name)
                      for base in ('/opt', '/tools', os.path.expanduser('~'))
                      for root_dir_name in VIVADO_ROOT_DIR_NAMES]

    for root_base in root_bases:
        candidates += vivado_layout_candidates(root_base, version, exe_name)

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def clean_proj_dir(proj_dir, force):
    """Deletes all contents of proj_dir except .keep (recreates proj_dir if missing)."""
    if not force and not git_vivado.accept_warning('All contents of %s will be permanently deleted.' % proj_dir):
        sys.exit()

    if not os.path.isdir(proj_dir):
        os.makedirs(proj_dir)
        print('INFO: Created empty %s' % proj_dir)
        return

    for entry in os.listdir(proj_dir):
        if entry == '.keep':
            continue
        entry_path = os.path.join(proj_dir, entry)
        if os.path.islink(entry_path):
            os.unlink(entry_path)
        elif os.path.isdir(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.remove(entry_path)
    print('INFO: Cleaned %s' % proj_dir)


def run_vivado_tcl(vivado_cmd, script_dir, tcl_name, xpr_path):
    """Runs a batch-mode vivado tcl script (export_xsa.tcl / archive_project.tcl) against xpr_path."""
    vivado_cmd = vivado_cmd.replace('\\', '/')
    script_path = os.path.join(script_dir, tcl_name).replace('\\', '/')
    xpr_path = xpr_path.replace('\\', '/')
    cmd = "%s -mode batch -source %s -notrace -tclargs -x %s" % (vivado_cmd, script_path, xpr_path)
    return os.system(cmd)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    project_name = os.path.basename(os.path.abspath(os.path.join(script_dir, '..')))

    config = git_vivado.configparser.ConfigParser()
    config.read(os.path.join(script_dir, "config.ini"))
    operating_system = platform.system()
    config_settings = config[operating_system]

    default_repo_path = os.path.abspath(os.path.join(script_dir, '..'))
    default_xpr_path = os.path.abspath(os.path.join(script_dir, '..', 'proj', '%s.xpr' % project_name))
    default_version = config_settings['VivadoVersion']

    parser = argparse.ArgumentParser(
        description='Cleans the proj/ directory and, optionally, (re)creates and/or builds the Vivado project',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-f', dest='force', default=False, action='store_true',
                         help='Skip confirmation prompts')
    parser.add_argument('-r', dest='repo_path', type=str, default=default_repo_path,
                         help='Path to target repository\nDefault = %s' % default_repo_path)
    parser.add_argument('-x', dest='xpr_path', type=str, default=default_xpr_path,
                         help='Path to XPR file\nDefault = %s' % default_xpr_path)
    parser.add_argument('-v', dest='version', type=str, default=default_version,
                         help='Vivado version number 20##.#\nDefault = %s' % default_version)
    parser.add_argument('--clean', dest='clean', default=False, action='store_true',
                         help='Delete all contents of the proj/ directory before doing anything else')
    parser.add_argument('--checkout', dest='checkout', default=False, action='store_true',
                         help='(Re)create the Vivado project only (no build)')
    parser.add_argument('--build', dest='build', default=False, action='store_true',
                         help='Create (if needed) and build the whole project: synth -> impl -> write_bitstream.\n'
                              'Takes precedence over --checkout if both are given.')
    parser.add_argument('--xsa', dest='xsa', default=False, action='store_true',
                         help='Export a fixed, bitstream-included hardware platform (.xsa) to <repo>/hw_handoff.\n'
                              'Requires a built project (use with --build, or run separately after one).')
    parser.add_argument('--archive', dest='archive', default=False, action='store_true',
                         help='Create a project release ZIP archive under <repo>/release.\n'
                              'Can be used with or without --build (only needs project sources).')
    args = parser.parse_args()

    if not (args.clean or args.checkout or args.build or args.xsa or args.archive):
        parser.error('Nothing to do: specify at least one of --clean, --checkout, --build, --xsa, --archive')

    repo_path = os.path.abspath(os.path.join(os.getcwd(), args.repo_path))
    xpr_path = os.path.abspath(os.path.join(os.getcwd(), args.xpr_path))
    proj_dir = os.path.dirname(xpr_path)

    if args.clean:
        clean_proj_dir(proj_dir, args.force)

    if args.checkout or args.build or args.xsa or args.archive:
        vivado_cmd = find_vivado_cmd(args.version, config_settings.get('VivadoInstallPath'))
        if not vivado_cmd:
            print('Error: Could not locate Vivado %s.' % args.version)
            print('       Checked config.ini path: %s' % config_settings.get('VivadoInstallPath'))
            print('       Checked root directories %s across all available drives/locations.' % VIVADO_ROOT_DIR_NAMES)
            sys.exit(1)
        print('INFO: Using Vivado at %s' % vivado_cmd)

    if args.checkout or args.build:
        if os.path.isfile(xpr_path):
            print('Error: cannot check out repo when project exists; re-run with --clean to remove %s first' % proj_dir)
            sys.exit(1)

        funcargs = {
            'script_dir': script_dir,
            'force': args.force,
            'repo_path': repo_path,
            'xpr_path': xpr_path,
            'version': args.version,
            'vivado_cmd': vivado_cmd,
            'build': args.build,
            'DEBUG_NO_VIVADO': False,
            'DEBUG_VIVADO_TCL_TRACE': False,
        }
        git_vivado.do_checkout(funcargs)

    # --xsa and --archive operate on an existing project (just checked out/built above,
    # or already present from a prior run) and can be combined freely with each other.
    if args.xsa or args.archive:
        if not os.path.isfile(xpr_path):
            print('Error: %s does not exist; run with --checkout or --build first' % xpr_path)
            sys.exit(1)

    if args.xsa:
        print('INFO: Exporting hardware platform (.xsa)')
        if run_vivado_tcl(vivado_cmd, script_dir, 'export_xsa.tcl', xpr_path) != 0:
            print('Error: xsa export failed')
            sys.exit(1)

    if args.archive:
        print('INFO: Creating project release archive')
        if run_vivado_tcl(vivado_cmd, script_dir, 'archive_project.tcl', xpr_path) != 0:
            print('Error: project archive failed')
            sys.exit(1)
