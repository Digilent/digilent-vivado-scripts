# PYTHON 3.X.X REQUIRED!!!
# TODO: ctrl-f for other TODOs
# TODO: pass vivado version to TCL scripts

import os
import sys
import configparser
import argparse
import platform

DEBUG_NO_VIVADO = False
DEBUG_VIVADO_TCL_TRACE = False

def accept_warning(s):
	c = ''
	d = {'Y': True, 'y': True, 'N': False, 'n': False}
	while not c in d:
		c = input('Warning: %s Y/N? ' % s)
	return d[c]

	# def do_checkin(script_dir, args):
def do_checkin(args):
	global DEBUG_NO_VIVADO
	global DEBUG_VIVADO_TCL_TRACE
	
	vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
	script_path = os.path.join(args['script_dir'], 'digilent_vivado_checkin.tcl').replace('\\', '/')
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
		os.system("%s -mode batch -source %s%s -tclargs %s %s %s" % (vivado_cmd, script_path, notrace, xpr_path, repo_path, version))
	
def do_checkout(args):
	global DEBUG_NO_VIVADO
	global DEBUG_VIVADO_TCL_TRACE
	
	vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
	script_path = os.path.join(args['script_dir'], 'digilent_vivado_checkout.tcl').replace('\\', '/')
	xpr_path    = args['xpr_path'].replace('\\', '/')
	repo_path   = args['repo_path'].replace('\\', '/')
	version     = args['version'].replace('\\', '/')
	
	if not args['force'] and not accept_warning('Files and directories contained in %s may be overwritten. Do you wish to continue?' % os.path.dirname(xpr_path)):
		sys.exit()
	
	print('Checking out project %s from repo %s' % (os.path.basename(xpr_path), os.path.basename(repo_path)))
	
	if DEBUG_NO_VIVADO:
		print ('vivado_cmd: %s' % vivado_cmd)
		print ('script_path: %s' % script_path)
		print ('xpr_path: %s' % xpr_path)
		print ('repo_path: %s' % repo_path)
		print ('version: %s' % version)
	else:
		notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
		os.system("%s -mode batch -source %s%s -tclargs %s %s %s" % (vivado_cmd, script_path, notrace, xpr_path, repo_path, version))
	
def do_release(script_dir, config, ):
	global DEBUG_NO_VIVADO
	global DEBUG_VIVADO_TCL_TRACE
	
	vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
	script_path = os.path.join(args['script_dir'], 'digilent_vivado_release.tcl').replace('\\', '/')
	xpr_path    = args['xpr_path'].replace('\\', '/')
	repo_path   = args['repo_path'].replace('\\', '/')
	zip_path    = args['zip_path'].replace('\\', '/')
	version     = args['version'].replace('\\', '/')
		
	if not args['force'] and not accept_warning('If %s exists, it will be overwritten. Do you wish to continue?' % zip_path):
		sys.exit()
	
	print('Creating release %s from project %s' % (os.path.basename(zip_path), os.path.basename(xpr_path)))
	
	if DEBUG_NO_VIVADO:
		print ('vivado_cmd: %s' % vivado_cmd)
		print ('script_path: %s' % script_path)
		print ('xpr_path: %s' % xpr_path)
		print ('zip_path: %s' % zip_path)
		print ('repo_path: %s' % repo_path)
		print ('version: %s' % version)
	else:
		notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
		os.system("%s -mode batch -source %s%s -tclargs %s %s %s" % (vivado_cmd, script_path, notrace, xpr_path, repo_path, version))

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
	releases_dir = os.path.abspath(os.path.join(script_dir, '..', 'releases'))
	default_zip_path = os.path.abspath(os.path.join(releases_dir, '%s-%s.zip' % (project_name, default_version)))

	# Parse SYS.ARGV
	parser = argparse.ArgumentParser(description='Handles vivado project git repo operations')
	parser.add_argument('-f', dest='force', default=False, action='store_true', help='Force overwrite of existing files and folders')
	subparsers = parser.add_subparsers(help='sub-command help')

	# Checkin Arguments
	parser_checkin = subparsers.add_parser('checkin', help='Checks in XPR to REPO', formatter_class=argparse.RawTextHelpFormatter)
	parser_checkin.set_defaults(func=do_checkin)
	# Optional Args
	parser_checkin.add_argument('-r', dest='repo_path', type=str, default=default_repo_path, help='Path to target repository from\nDefault = %s' % (default_repo_path))
	parser_checkin.add_argument('-x', dest='xpr_path',  type=str, default=default_xpr_path,  help='Path to XPR file\nDefault = %s' % (default_xpr_path))
	parser_checkin.add_argument('-v', dest='version',   type=str, default=default_version,   help='Vivado version number 20##.#\nDefault = %s' % (default_version))

	# Checkout Arguments
	parser_checkout = subparsers.add_parser('checkout', help='Checks out XPR from REPO', formatter_class=argparse.RawTextHelpFormatter)
	parser_checkout.set_defaults(func=do_checkout)
	# Optional Args
	parser_checkout.add_argument('-r', dest='repo_path', type=str, default=default_repo_path, help='Path to target repository from\nDefault = %s' % (default_repo_path))
	parser_checkout.add_argument('-x', dest='xpr_path',  type=str, default=default_xpr_path,  help='Path to XPR file\nDefault = %s' % (default_xpr_path))
	parser_checkout.add_argument('-v', dest='version',   type=str, default=default_version,   help='Vivado version number 20##.#\nDefault = %s' % (default_version))

	# Release Arguments
	parser_release = subparsers.add_parser('release', help='Creates release ZIP from XPR', formatter_class=argparse.RawTextHelpFormatter)
	parser_release.set_defaults(func=do_release)
	# Optional Args
	parser_release.add_argument('-z', dest='zip_path',  type=str, default=default_zip_path,  help='Path to new release archive ZIP file\nDefault = %s' % (default_zip_path))
	parser_release.add_argument('-r', dest='repo_path', type=str, default=default_repo_path, help='Path to target repository from\nDefault = %s' % (default_repo_path))
	parser_release.add_argument('-x', dest='xpr_path',  type=str, default=default_xpr_path,  help='Path to XPR file\nDefault = %s' % (default_xpr_path))
	parser_release.add_argument('-v', dest='version',   type=str, default=default_version,   help='Vivado version number 20##.#\nDefault = %s' % (default_version))

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
			print('Error: cannot check out repo when project exists; Please clean out the %s/proj directory' % (repo_path))
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
	
	if hasattr(args, 'version'):
		funcargs['vivado_cmd'] = os.path.join(os.path.abspath(config_settings['VivadoInstallPath']), args.version, 'bin', 'vivado')
		funcargs['version'] = args.version
		if not os.path.isfile(funcargs['vivado_cmd']):
			print('Error: Vivado not installed at %s' % funcargs['vivado_cmd'])
			sys.exit()
#	for key in funcargs:
#		print(key, ':', funcargs[key])
	args.func(funcargs)
