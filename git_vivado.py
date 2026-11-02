"""
git_vivado.py

Move a Vivado project between its working form (the generated proj/
directory, not version-controlled) and its source form (the repository).

  checkin  - checkin.tcl writes the sources of an existing project to the repo
  checkout - checkout.tcl recreates the project from the repo, optionally
             building it

Both are thin wrappers around a vivado batch-mode command line and are
importable, so clean_build.py drives the same code paths.

The Vivado install path and version are saved to <repo>/config.ini the first
time they are used, so later runs need no flags. The file is local to each
machine and ignored by the repository.

Note: Python 3 is required.

Sections: helpers, Vivado discovery, local settings, checkin, checkout,
command line.
"""

import os
import sys
import configparser
import argparse
import platform
import re
import string
import ctypes


# Install root names in search order (Vivado 2025.1+ uses AMDDesignTools)
VIVADO_ROOT_DIR_NAMES = ['AMDDesignTools', 'Xilinx']

CONFIG_NAME = 'config.ini'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def accept_warning(s):
    """Ask the user to confirm a destructive action, repeat until Y or N."""
    c = ''
    d = {'Y': True, 'y': True, 'N': False, 'n': False}
    while c not in d:
        c = input('Warning: %s Y/N? ' % s)
    return d[c]


def to_posix(path):
    """Return path with forward slashes, which vivado accepts on every OS."""
    return path.replace('\\', '/')


# ---------------------------------------------------------------------------
# Vivado discovery
# ---------------------------------------------------------------------------

def list_windows_drives():
    """Return the available drive roots on Windows, e.g. ['C:\\\\', 'D:\\\\']."""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drives.append('%s:\\' % letter)
    return drives


def vivado_layout_candidates(root_base, version, exe_name):
    """Return the two known install layouts under an install root.

    E:\\AMDDesignTools, 2025.2:
      - E:\\AMDDesignTools\\Vivado\\2025.2\\bin\\vivado.bat  (older)
      - E:\\AMDDesignTools\\2025.2\\Vivado\\bin\\vivado.bat  (2025.1+)
    """
    return [
        os.path.join(root_base, 'Vivado', version, 'bin', exe_name),
        os.path.join(root_base, version, 'Vivado', 'bin', exe_name),
    ]


def search_roots(install_path=None):
    """Return the install roots to search, the configured one first."""
    roots = []
    if install_path:
        install_path = os.path.abspath(install_path)
        roots += [install_path, os.path.dirname(install_path)]

    if platform.system() == 'Windows':
        bases = list_windows_drives()
    else:
        bases = ['/opt', '/tools', os.path.expanduser('~')]
    roots += [os.path.join(base, name) for base in bases for name in VIVADO_ROOT_DIR_NAMES]
    return roots


def find_vivado_cmd(version, install_path=None):
    """Return the vivado command for version, or None if not found.

    Search order:
      1. install_path, and its parent for the older ".../Vivado" style
      2. every VIVADO_ROOT_DIR_NAMES entry on all drives (Windows) or under
         /opt, /tools and ~ (Linux)
    """
    exe_name = 'vivado.bat' if platform.system() == 'Windows' else 'vivado'
    for root in search_roots(install_path):
        for candidate in vivado_layout_candidates(root, version, exe_name):
            if os.path.isfile(candidate):
                return candidate
    return None


def find_latest_version(install_path=None):
    """Return the newest installed Vivado version, or None if there is none."""
    found = set()
    for root in search_roots(install_path):
        # Names such as 2025.2 in the root (2025.1+) or in <root>/Vivado (older)
        for parent in (root, os.path.join(root, 'Vivado')):
            if not os.path.isdir(parent):
                continue
            for name in os.listdir(parent):
                if re.fullmatch(r'\d{4}\.\d+', name) and find_vivado_cmd(name, root):
                    found.add(name)
    return max(found, key=lambda v: tuple(int(p) for p in v.split('.')), default=None)


def install_root_of(vivado_cmd):
    """Return the install root of a vivado command, for both layouts."""
    root = vivado_cmd
    for _ in range(4):
        root = os.path.dirname(root)
    return root


# ---------------------------------------------------------------------------
# Local settings
# ---------------------------------------------------------------------------

def config_path(script_dir):
    """Return the path of config.ini, in the repository that holds the scripts."""
    return os.path.abspath(os.path.join(script_dir, '..', CONFIG_NAME))


def load_config(script_dir):
    """Return the saved install_path and version, empty strings when unset."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(config_path(script_dir))
    section = parser['Vivado'] if parser.has_section('Vivado') else {}
    return {'install_path': section.get('InstallPath', ''),
            'version': section.get('Version', '')}


def save_config(script_dir, install_path, version):
    """Save the settings to config.ini, return True when the file changed."""
    install_path = to_posix(install_path)
    if load_config(script_dir) == {'install_path': install_path, 'version': version}:
        return False
    parser = configparser.ConfigParser(interpolation=None)
    parser['Vivado'] = {'InstallPath': install_path, 'Version': version}
    with open(config_path(script_dir), 'w') as f:
        f.write('# Local settings, written by git_vivado.py and clean_build.py.\n')
        parser.write(f)
    return True


def locate_vivado(script_dir, version=None, install_path=None):
    """Return (vivado_cmd, version), exit if Vivado is not found.

    Flags win over config.ini, which wins over the defaults. The result is
    saved when a flag was given or config.ini does not exist yet.
    """
    saved = load_config(script_dir)
    given = bool(version or install_path)
    install_path = install_path or saved['install_path']
    version = version or saved['version'] or find_latest_version(install_path)
    if not version:
        print('Error: No Vivado installation found.')
        print('       Use -i <install root> to point at it.')
        sys.exit(1)

    vivado_cmd = find_vivado_cmd(version, install_path)
    if not vivado_cmd:
        print('Error: Could not locate Vivado %s.' % version)
        print('       Checked install path: %s' % (install_path or 'none'))
        print('       Checked root directories %s on all available drives/locations.'
              % VIVADO_ROOT_DIR_NAMES)
        print('       Use -i <install root> to point at it.')
        sys.exit(1)

    if given or not os.path.isfile(config_path(script_dir)):
        if save_config(script_dir, install_root_of(vivado_cmd), version):
            print('INFO: Saved Vivado settings to %s' % config_path(script_dir))
    return vivado_cmd, version


# ---------------------------------------------------------------------------
# Checkin
# ---------------------------------------------------------------------------

def do_checkin(args):
    """Write an existing Vivado project back into the repository.

    args is a dict with script_dir, vivado_cmd, xpr_path, repo_path, version,
    force and the two DEBUG_ flags. Prompts first unless force is set.
    """
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    DEBUG_VIVADO_TCL_TRACE = args['DEBUG_VIVADO_TCL_TRACE']

    vivado_cmd = to_posix(args['vivado_cmd'])
    script_path = to_posix(os.path.join(args['script_dir'], 'checkin.tcl'))
    xpr_path = to_posix(args['xpr_path'])
    repo_path = to_posix(args['repo_path'])
    version = to_posix(args['version'])

    if not args['force'] and not accept_warning(
            'Files and directories contained in %s may be overwritten. '
            'Do you wish to continue?' % repo_path):
        sys.exit()

    print('Checking in project %s to repo %s'
          % (os.path.basename(xpr_path), os.path.basename(repo_path)))

    if DEBUG_NO_VIVADO:
        print('vivado_cmd: %s' % vivado_cmd)
        print('script_path: %s' % script_path)
        print('xpr_path: %s' % xpr_path)
        print('repo_path: %s' % repo_path)
        print('version: %s' % version)
    else:
        notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
        return os.system("%s -mode batch -source %s%s -tclargs -x %s -r %s -v %s"
                         % (vivado_cmd, script_path, notrace, xpr_path, repo_path, version))


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

def do_checkout(args):
    """Recreate a Vivado project from the repository, optionally building it.

    args is a dict with script_dir, vivado_cmd, xpr_path, repo_path, version,
    build, force and the two DEBUG_ flags. Optional keys:
      extra_tclargs - raw tokens appended to the -tclargs of checkout.tcl
      vivado_opts   - raw vivado options placed before -mode batch
      runner        - callable run with the command line, default os.system

    Return the exit status. Prompts first unless force is set.
    """
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    DEBUG_VIVADO_TCL_TRACE = args['DEBUG_VIVADO_TCL_TRACE']

    vivado_cmd = to_posix(args['vivado_cmd'])
    script_path = to_posix(os.path.join(args['script_dir'], 'checkout.tcl'))
    xpr_path = to_posix(args['xpr_path'])
    repo_path = to_posix(args['repo_path'])
    version = to_posix(args['version'])
    build = args['build']

    # Appended verbatim, e.g. '-D MY_OPTION 1' for the BD script
    extra_tclargs = args.get('extra_tclargs', '')
    # Needed by concurrent runs, e.g. '-journal <path> -log <path>'
    vivado_opts = args.get('vivado_opts', '')
    # Concurrent callers capture the output per project instead of os.system
    runner = args.get('runner') or os.system

    if not args['force'] and not accept_warning(
            'Files and directories contained in %s may be overwritten. '
            'Do you wish to continue?' % os.path.dirname(xpr_path)):
        sys.exit()

    print('Checking out project %s from repo %s'
          % (os.path.basename(xpr_path), os.path.basename(repo_path)))
    notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
    cmd = "%s%s -mode batch -source %s%s -tclargs -x %s -r %s -v %s%s%s" % (
        vivado_cmd,
        ' %s' % vivado_opts if vivado_opts else '',
        script_path,
        notrace,
        xpr_path,
        repo_path,
        version,
        ' -b' if build else '',
        ' %s' % extra_tclargs if extra_tclargs else ''
    )
    if DEBUG_NO_VIVADO:
        print('vivado_cmd: %s' % vivado_cmd)
        print('script_path: %s' % script_path)
        print('xpr_path: %s' % xpr_path)
        print('repo_path: %s' % repo_path)
        print('version: %s' % version)
        print('build: %s' % build)
        print('extra_tclargs: %s' % extra_tclargs)
        print(cmd)
        return 0
    # The status lets callers detect a failed checkout or build
    return runner(cmd)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def build_parser(default_repo_path, default_xpr_path, default_version):
    """Return the parser with the checkin and checkout subcommands."""
    parser = argparse.ArgumentParser(description='Handles vivado project git repo operations')
    parser.add_argument(
        '-f',
        dest='force',
        default=False,
        action='store_true',
        help='Force overwrite of existing files and folders'
    )
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_checkin = subparsers.add_parser(
        'checkin',
        help='Checks in XPR to REPO',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_checkin.set_defaults(func=do_checkin)

    parser_checkout = subparsers.add_parser(
        'checkout',
        help='Checks out XPR from REPO',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_checkout.set_defaults(func=do_checkout)

    # Both subcommands share the path and version options
    for sub in (parser_checkin, parser_checkout):
        sub.add_argument(
            '-r',
            dest='repo_path',
            type=str,
            default=default_repo_path,
            help='Path to target repository from\nDefault = %s' % (default_repo_path)
        )
        sub.add_argument(
            '-x',
            dest='xpr_path',
            type=str,
            default=default_xpr_path,
            help='Path to XPR file\nDefault = %s' % (default_xpr_path)
        )
        sub.add_argument(
            '-v',
            dest='version',
            type=str,
            default=None,
            help='Vivado version number 20##.#\nDefault = %s' % (default_version)
        )
        sub.add_argument(
            '-i',
            dest='install_path',
            type=str,
            default=None,
            help='Vivado install root, e.g. <drive>/AMDDesignTools\nDefault = from config.ini'
        )

    parser_checkout.add_argument(
        '-b',
        dest='build',
        default=False,
        action='store_true',
        help='Build the project after checkout\nDefault = false'
    )
    return parser


def main():
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    project_name = os.path.basename(os.path.abspath(os.path.join(script_dir, '..')))

    # Defaults assume this script is a submodule of the target repository
    default_repo_path = os.path.abspath(os.path.join(script_dir, '..'))
    default_xpr_path = os.path.abspath(
        os.path.join(script_dir, '..', 'proj', '%s.xpr' % project_name))
    default_version = load_config(script_dir)['version'] or 'newest installed'

    parser = build_parser(default_repo_path, default_xpr_path, default_version)
    args = parser.parse_args()

    funcargs = {'script_dir': script_dir}

    if not hasattr(args, 'func'):
        print("Please select a subcommand to execute. See this command's help page")
        sys.exit()

    if hasattr(args, 'force'):
        funcargs['force'] = args.force

    if hasattr(args, 'build'):
        funcargs['build'] = args.build

    if hasattr(args, 'repo_path'):
        funcargs['repo_path'] = os.path.abspath(os.path.join(os.getcwd(), args.repo_path))

    if hasattr(args, 'xpr_path'):
        if args.xpr_path[-4:] != '.xpr':
            print('Error: xpr_path argument must end in .xpr')
            sys.exit()
        funcargs['xpr_path'] = os.path.abspath(os.path.join(os.getcwd(), args.xpr_path))
        if (args.func == do_checkout and os.path.isfile(funcargs['xpr_path'])
                or os.path.isdir(funcargs['xpr_path'])):
            print('Error: cannot check out repo when project exists; '
                  'Please clean out the %s/proj directory' % (funcargs['repo_path']))
            sys.exit()

    if hasattr(args, 'version'):
        funcargs['vivado_cmd'], funcargs['version'] = locate_vivado(
            script_dir, args.version, args.install_path)

    if hasattr(args, 'temp_directory'):
        funcargs['temp_directory'] = args.temp_directory

    funcargs['DEBUG_NO_VIVADO'] = False
    funcargs['DEBUG_VIVADO_TCL_TRACE'] = False

    # A failed vivado run makes the script exit non-zero
    sys.exit(1 if args.func(funcargs) else 0)


if __name__ == "__main__":
    main()
