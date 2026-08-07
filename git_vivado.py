# PYTHON 3.X.X REQUIRED!!!
"""
git_vivado.py

Moves a Vivado project between its working form (a project directory full of
generated files, which does not belong in version control) and its source
form (the tracked contents of the repository).

Two operations, each a thin wrapper that assembles a vivado batch-mode
command line around the matching Tcl script:

  checkin  -- checkin.tcl reads an existing project and writes the sources
              that describe it back into the repository
  checkout -- checkout.tcl reads those sources and recreates the project,
              optionally building it as well

Both are also importable, so other tooling (clean_build.py) can drive the
same code paths rather than duplicating the command-line construction.
"""

import os
import sys
import configparser
import argparse
import platform

def accept_warning(s):
    """Asks the user to confirm a destructive action, returning their answer.

    Repeats the prompt until a recognised response is given, so a stray
    keypress cannot be read as consent.
    """
    c = ''
    d = {'Y': True, 'y': True, 'N': False, 'n': False}
    while c not in d:
        c = input('Warning: %s Y/N? ' % s)
    return d[c]

def do_checkin(args):
    """Writes an existing Vivado project back into the repository.

    Expects a dict with script_dir, vivado_cmd, xpr_path, repo_path, version,
    force and the two DEBUG_ flags. Prompts before overwriting unless force
    is set, since this rewrites tracked files in repo_path.
    """
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    DEBUG_VIVADO_TCL_TRACE = args['DEBUG_VIVADO_TCL_TRACE']
    
    vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
    script_path = os.path.join(args['script_dir'], 'checkin.tcl').replace('\\', '/')
    xpr_path    = args['xpr_path'].replace('\\', '/')
    repo_path   = args['repo_path'].replace('\\', '/')
    version     = args['version'].replace('\\', '/')
    
    if not args['force'] and not accept_warning('Files and directories contained in %s may be overwritten. Do you wish to continue?' % repo_path):
        sys.exit()
        
    print('Checking in project %s to repo %s' % (os.path.basename(xpr_path), os.path.basename(repo_path)))
    
    if DEBUG_NO_VIVADO:
        print ('vivado_cmd: %s' % vivado_cmd)
        print ('script_path: %s' % script_path)
        print ('xpr_path: %s' % xpr_path)
        print ('repo_path: %s' % repo_path)
        print ('version: %s' % version)
    else:
        notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
        os.system("%s -mode batch -source %s%s -tclargs -x %s -r %s -v %s" % (vivado_cmd, script_path, notrace, xpr_path, repo_path, version))
    
def do_checkout(args):
    """Recreates a Vivado project from the repository, optionally building it.

    Expects a dict with script_dir, vivado_cmd, xpr_path, repo_path, version,
    build, force and the two DEBUG_ flags. These keys are optional:

      extra_tclargs -- raw tokens appended to checkout.tcl's -tclargs
      vivado_opts   -- raw vivado options placed before -mode batch
      runner        -- callable invoked with the finished command line,
                       defaulting to os.system

    Returns the command's exit status. Prompts before overwriting the project
    directory unless force is set.
    """
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    DEBUG_VIVADO_TCL_TRACE = args['DEBUG_VIVADO_TCL_TRACE']
    
    vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
    script_path = os.path.join(args['script_dir'], 'checkout.tcl').replace('\\', '/')
    xpr_path    = args['xpr_path'].replace('\\', '/')
    repo_path   = args['repo_path'].replace('\\', '/')
    version     = args['version'].replace('\\', '/')
    build       = args['build']
    # Extra raw -tclargs tokens appended verbatim to the checkout.tcl call,
    # e.g. '-D MY_OPTION 1' to set a global Tcl variable a project's own BD
    # script can read (see checkout.tcl's -D handling). Optional; defaults
    # to nothing so existing callers are unaffected.
    extra_tclargs = args.get('extra_tclargs', '')
    # Extra raw vivado command-line options inserted before -mode batch,
    # e.g. '-journal <path> -log <path>'. Needed when several vivado
    # processes run concurrently, because they would otherwise all write to
    # vivado.jou/vivado.log in the same working directory. Optional.
    vivado_opts = args.get('vivado_opts', '')
    # Callable used to actually run the assembled command line, defaulting to
    # os.system (unchanged behavior). Concurrent callers substitute a runner
    # that captures output per project, since os.system lets every process
    # write straight to the shared console.
    runner = args.get('runner') or os.system

    if not args['force'] and not accept_warning('Files and directories contained in %s may be overwritten. Do you wish to continue?' % os.path.dirname(xpr_path)):
        sys.exit()
    
    print('Checking out project %s from repo %s' % (os.path.basename(xpr_path), os.path.basename(repo_path)))
    notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
    cmd = "%s%s -mode batch -source %s%s -tclargs -x %s -r %s -v %s%s%s" % (
        vivado_cmd,
        ' %s' % vivado_opts if vivado_opts else '',
        script_path,
        notrace,
        # arguments
        xpr_path,
        repo_path,
        version,
        ' -b' if build else '',
        ' %s' % extra_tclargs if extra_tclargs else ''
    )
    if DEBUG_NO_VIVADO:
        print ('vivado_cmd: %s' % vivado_cmd)
        print ('script_path: %s' % script_path)
        print ('xpr_path: %s' % xpr_path)
        print ('repo_path: %s' % repo_path)
        print ('version: %s' % version)
        print ('build: %s' % build)
        print ('extra_tclargs: %s' % extra_tclargs)
        print(cmd)
        return 0
    # Returning the exit status lets callers detect a failed checkout/build.
    # Previously discarded; existing callers that ignore it are unaffected.
    return runner(cmd)

if __name__ == "__main__":
    # Parse CONFIG.INI
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    project_name = os.path.basename(os.path.abspath(os.path.join(script_dir, '..')))
    config = configparser.ConfigParser()
    config.read(os.path.join(script_dir, "config.ini"))
    operating_system = platform.system()
    config_settings = config[operating_system]
    
    # Default arguments assume that this script is contained in a submodule within the target repository
    default_repo_path = os.path.abspath(os.path.join(script_dir, '..'))
    default_xpr_path = os.path.abspath(os.path.join(script_dir, '..', 'proj', '%s.xpr' % project_name))
    default_version = config_settings['VivadoVersion']
    
    # Parse SYS.ARGV
    parser = argparse.ArgumentParser(description='Handles vivado project git repo operations')
    parser.add_argument(
        '-f',
        dest='force',
        default=False,
        action='store_true',
        help='Force overwrite of existing files and folders'
    )
    subparsers = parser.add_subparsers(help='sub-command help')

    # Checkin Arguments
    parser_checkin = subparsers.add_parser(
        'checkin',
        help='Checks in XPR to REPO',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_checkin.set_defaults(func=do_checkin)
    # Optional Args
    parser_checkin.add_argument(
        '-r',
        dest='repo_path',
        type=str,
        default=default_repo_path,
        help='Path to target repository from\nDefault = %s' % (default_repo_path)
    )
    parser_checkin.add_argument(
        '-x',
        dest='xpr_path',
        type=str,
        default=default_xpr_path,
        help='Path to XPR file\nDefault = %s' % (default_xpr_path)
    )
    parser_checkin.add_argument(
        '-v',
        dest='version',
        type=str,
        default=default_version,
        help='Vivado version number 20##.#\nDefault = %s' % (default_version)
    )

    # Checkout Arguments
    parser_checkout = subparsers.add_parser(
        'checkout',
        help='Checks out XPR from REPO',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_checkout.set_defaults(func=do_checkout)
    # Optional Args
    parser_checkout.add_argument(
        '-r',
        dest='repo_path',
        type=str,
        default=default_repo_path,
        help='Path to target repository from\nDefault = %s' % (default_repo_path)
    )
    parser_checkout.add_argument(
        '-x',
        dest='xpr_path', 
        type=str,
        default=default_xpr_path, 
        help='Path to XPR file\nDefault = %s' % (default_xpr_path)
    )
    parser_checkout.add_argument(
        '-v',
        dest='version',  
        type=str,
        default=default_version,  
        help='Vivado version number 20##.#\nDefault = %s' % (default_version)
    )
    parser_checkout.add_argument(
        '-b',
        dest='build',
        default=False,
        action='store_true',
        help='Build the project after checkout\nDefault = false'
    )

    # Parse Arguments
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
        if args.func == do_checkout and os.path.isfile(funcargs['xpr_path']) or os.path.isdir(funcargs['xpr_path']):
            # TODO: add warning about overwriting existing project
            # TODO: add clean and overwrite process
            # TODO: move project_info.tcl to repo root
            print('Error: cannot check out repo when project exists; Please clean out the %s/proj directory' % (funcargs['repo_path']))
            sys.exit()
    
    if hasattr(args, 'version'):
        funcargs['vivado_cmd'] = os.path.join(os.path.abspath(config_settings['VivadoInstallPath']), args.version, 'bin', 'vivado')
        funcargs['version'] = args.version
        if not os.path.isfile(funcargs['vivado_cmd']):
            print('Error: Vivado not installed at %s' % funcargs['vivado_cmd'])
            sys.exit()

    if hasattr(args, 'temp_directory'):
        funcargs['temp_directory'] = args.temp_directory

    DEBUG_NO_VIVADO = False
    DEBUG_VIVADO_TCL_TRACE = False
    funcargs['DEBUG_NO_VIVADO'] = DEBUG_NO_VIVADO
    funcargs['DEBUG_VIVADO_TCL_TRACE'] = DEBUG_VIVADO_TCL_TRACE

    args.func(funcargs)
