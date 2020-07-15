# PYTHON 3.X.X REQUIRED!!!

import os
import sys
import configparser
import argparse
import platform

from release import do_release

def accept_warning(s):
    c = ''
    d = {'Y': True, 'y': True, 'N': False, 'n': False}
    while c not in d:
        c = input('Warning: %s Y/N? ' % s)
    return d[c]

def do_checkin(args):
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    DEBUG_VIVADO_TCL_TRACE = args['DEBUG_VIVADO_TCL_TRACE']
    
    vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
    script_path = os.path.join(args['script_dir'], 'digilent_vivado_checkin.tcl').replace('\\', '/')
    xpr_path    = args['xpr_path'].replace('\\', '/')
    repo_path   = args['repo_path'].replace('\\', '/')
    version     = args['version'].replace('\\', '/')
    workspace   = args['workspace'].replace('\\', '/')
    no_hdf      = ' -no_hdf' if args['no_hdf'] else ''
    
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
        os.system("%s -mode batch -source %s%s -tclargs -x %s -r %s -v %s -w %s%s" % (vivado_cmd, script_path, notrace, xpr_path, repo_path, version, workspace, no_hdf))
    
def do_checkout(args):
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    DEBUG_VIVADO_TCL_TRACE = args['DEBUG_VIVADO_TCL_TRACE']
    
    vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
    script_path = os.path.join(args['script_dir'], 'digilent_vivado_checkout.tcl').replace('\\', '/')
    xpr_path    = args['xpr_path'].replace('\\', '/')
    repo_path   = args['repo_path'].replace('\\', '/')
    version     = args['version'].replace('\\', '/')
    workspace   = args['workspace'].replace('\\', '/')
    
    
    if not args['force'] and not accept_warning('Files and directories contained in %s may be overwritten. Do you wish to continue?' % os.path.dirname(xpr_path)):
        sys.exit()
    
    print('Checking out project %s from repo %s' % (os.path.basename(xpr_path), os.path.basename(repo_path)))
    notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
    cmd = "%s -mode batch -source %s%s -tclargs -x %s -r %s -v %s -w %s" % (
        vivado_cmd,
        script_path,
        notrace,
        # arguments
        xpr_path,
        repo_path,
        version,
        workspace
    )
    if DEBUG_NO_VIVADO:
        print ('vivado_cmd: %s' % vivado_cmd)
        print ('script_path: %s' % script_path)
        print ('xpr_path: %s' % xpr_path)
        print ('repo_path: %s' % repo_path)
        print ('version: %s' % version)
        print(cmd)
    else:
        os.system(cmd)

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
    
    idx = 0
    while os.path.exists( os.path.abspath(os.path.join(script_dir, '..', 'release_%d' % (idx))) ):
        idx += 1
    release_dir = os.path.abspath(os.path.join(script_dir, '..', 'release_%d' % (idx)))

    default_zip_path = os.path.abspath(os.path.join(release_dir, '%s-%s.zip' % (project_name, default_version)))
    default_temp_directory = os.path.abspath(os.path.join(release_dir, '%s-%s' % (project_name, default_version)))

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
    parser_checkin.add_argument(
        '-no_hdf',
        dest='no_hdf',
        default=False,
        action='store_true',
        help='Do not check in hardware handoff\n Default = not set (False)'
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

    # Release Arguments
    parser_release = subparsers.add_parser(
        'release',
        help='Creates release ZIP from XPR',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_release.set_defaults(func=do_release)
    # Optional Args
    parser_release.add_argument(
        '-z',
        dest='zip_path', 
        type=str,
        default=default_zip_path, 
        help='Path to new release archive ZIP file\nDefault = %s' % (default_zip_path)
    )
    parser_release.add_argument(
        '-r',
        dest='repo_path',
        type=str,
        default=default_repo_path,
        help='Path to target repository from\nDefault = %s' % (default_repo_path)
    )
    parser_release.add_argument(
        '-x',
        dest='xpr_path', 
        type=str,
        default=default_xpr_path, 
        help='Path to XPR file\nDefault = %s' % (default_xpr_path)
    )
    parser_release.add_argument(
        '-v',
        dest='version',  
        type=str,
        default=default_version,  
        help='Vivado version number 20##.#\nDefault = %s' % (default_version)
    )
    parser_release.add_argument(
        '-ws',
        dest='workspace',
        type=str,
        default=default_workspace_path,
        help='Path to SDK workspace\nDefault = %s' % (default_workspace_path)
    )
    parser_release.add_argument(
        '-temp',
        dest='temp_directory',
        type=str,
        default=default_temp_directory,
        help='Temp directory to store release intermediates\nDefault = %s' % (default_temp_directory)
    )

    # Parse Arguments
    args = parser.parse_args()

    funcargs = {'script_dir': script_dir}
    
    if not hasattr(args, 'func'):
        print("Please select a subcommand to execute. See this command's help page")
        sys.exit()
    
    if hasattr(args, 'force'):
        funcargs['force'] = args.force
    
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
    
    if hasattr(args, 'zip_path'):
        #if not os.path.dirname(args.zip_path):
            # TODO: add warning/confirmation to create directory structure
            # TODO: recursively create missing directories in zip_path
        if os.path.isfile(args.zip_path):
            # TODO: consider adding automatic renaming of release archive
            print("Error: Target ZIP archive already exists")
            sys.exit()
        funcargs['zip_path'] = os.path.abspath(os.path.join(os.getcwd(), args.zip_path))
    
    if hasattr(args, 'no_hdf'):
        funcargs['no_hdf'] = args.no_hdf
    
    if hasattr(args, 'workspace'):
        # TODO: check for workspace's existence
        funcargs['workspace'] = args.workspace

    if hasattr(args, 'version'):
        funcargs['vivado_cmd'] = os.path.join(os.path.abspath(config_settings['VivadoInstallPath']), args.version, 'bin', 'vivado')
        funcargs['version'] = args.version
        if not os.path.isfile(funcargs['vivado_cmd']):
            print('Error: Vivado not installed at %s' % funcargs['vivado_cmd'])
            sys.exit()
        funcargs['xsct_cmd'] = os.path.join(os.path.abspath(config_settings['SdkInstallPath']), args.version, 'bin', config_settings['XsctFile'])
        if not os.path.isfile(funcargs['xsct_cmd']):
            print('Error: XSCT not installed at %s' % funcargs['xsct_cmd'])
            sys.exit()

    if hasattr(args, 'temp_directory'):
        funcargs['temp_directory'] = args.temp_directory

    DEBUG_NO_VIVADO = False
    DEBUG_VIVADO_TCL_TRACE = False
    funcargs['DEBUG_NO_VIVADO'] = DEBUG_NO_VIVADO
    funcargs['DEBUG_VIVADO_TCL_TRACE'] = DEBUG_VIVADO_TCL_TRACE

    args.func(funcargs)
