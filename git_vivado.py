# PYTHON 3.X.X REQUIRED!!!

import os
import sys
import configparser
import argparse

DEBUG_NO_VIVADO = True

def accept_warning(s):
	c = ''
	d = {'Y': True, 'y': True, 'N': False, 'n': False}
	while not c in d:
		c = input('Warning: %s Y/N? ' % s)
	return d[c]

def do_checkin(script_dir, config, args):
	global DEBUG_NO_VIVADO
	
	if args.version == 'none':
		vivado_cmd = 'vivado'
	else:
		vivado_cmd = os.path.join(os.path.abspath(config['DEFAULT']['VivadoInstallPath']), args.version, 'bin', 'vivado')
	script_path = os.path.join(script_dir, 'digilent_vivado_checkin.tcl')
	if args.xpr_path == 'none':
		xpr_path = os.path.abspath(os.path.join(script_dir, '..', 'proj'))
	else:
		xpr_path = os.path.join(os.path.abspath(config['DEFAULT']['ProjectBasePath']), args.xpr_path)
	if default_repo_path != args.repo_path:
		repo_path = os.path.join(os.path.abspath(config['DEFAULT']['GithubBasePath']), args.repo_path)
	else:
		repo_path = args.repo_path
	
	vivado_cmd = vivado_cmd.replace('\\', '/')
	script_path = script_path.replace('\\', '/')
	xpr_path = xpr_path.replace('\\', '/')
	repo_path = repo_path.replace('\\', '/')
	
	if xpr_path[:-3] != '.xpr':
		print('Error: xpr_path argument must end in .xpr')
		sys.exit()
	
	if not accept_warning('Files and directories contained in %s may be deleted. Do you wish to continue?' % repo_path):
		sys.exit()
		
	print('Checking in project %s to repo %s' % (os.path.basename(xpr_path), os.path.basename(repo_path)))
		
	if DEBUG_NO_VIVADO:
		print ('vivado_cmd: %s' % vivado_cmd)
		print ('script_path: %s' % script_path)
		print ('xpr_path: %s' % xpr_path)
		print ('repo_path: %s' % repo_path)
	else:
		os.system("%s -mode batch -source %s -notrace -tclargs %s %s" % (vivado_cmd, script_path, xpr_path, repo_path))
	
def do_checkout(script_dir, config, args):
	global DEBUG_NO_VIVADO
	
	if args.version == 'none':
		vivado_cmd = 'vivado'
	else:
		vivado_cmd = os.path.join(os.path.abspath(config['DEFAULT']['VivadoInstallPath']), args.version, 'bin', 'vivado')
	script_path = os.path.join(script_dir, 'digilent_vivado_checkout.tcl')
	if args.xpr_path == 'none':
		xpr_path = os.path.abspath(os.path.join(script_dir, '..', 'proj'))
	else:
		xpr_path = os.path.join(os.path.abspath(config['DEFAULT']['ProjectBasePath']), args.xpr_path)
	if default_repo_path != args.repo_path:
		repo_path = os.path.join(os.path.abspath(config['DEFAULT']['GithubBasePath']), args.repo_path)
	else:
		repo_path = args.repo_path
	
	vivado_cmd = vivado_cmd.replace('\\', '/')
	script_path = script_path.replace('\\', '/')
	xpr_path = xpr_path.replace('\\', '/')
	repo_path = repo_path.replace('\\', '/')
	
	if xpr_path[:-3] != '.xpr':
		print('Error: xpr_path argument must end in .xpr')
		sys.exit()
		
	if not accept_warning('Files and directories contained in %s may be deleted. Do you wish to continue?' % os.path.dirname(xpr_path)):
		sys.exit()
	
	print('Checking out project %s from repo %s' % (os.path.basename(xpr_path), os.path.basename(repo_path)))
	
	if DEBUG_NO_VIVADO:
		print ('vivado_cmd: %s' % vivado_cmd)
		print ('script_path: %s' % script_path)
		print ('xpr_path: %s' % xpr_path)
		print ('repo_path: %s' % repo_path)
	else:
		os.system("%s -mode batch -source %s -notrace -tclargs %s %s" % (vivado_cmd, script_path, xpr_path, repo_path))
	
def do_release(script_dir, config, args):
	global DEBUG_NO_VIVADO
	
	if args.version == 'none':
		vivado_cmd = 'vivado'
	else:
		vivado_cmd = os.path.join(os.path.abspath(config['DEFAULT']['VivadoInstallPath']), args.version, 'bin', 'vivado')
	script_path = os.path.join(script_dir, 'digilent_vivado_release.tcl')
	if args.xpr_path == 'none':
		xpr_path = os.path.abspath(os.path.join(script_dir, '..', 'proj'))
	else:
		xpr_path = os.path.join(os.path.abspath(config['DEFAULT']['ProjectBasePath']), args.xpr_path)
	zip_path = os.path.join(os.path.abspath(config['DEFAULT']['ProjectBasePath']), args.zip_path)
		
	vivado_cmd = vivado_cmd.replace('\\', '/')
	script_path = script_path.replace('\\', '/')
	xpr_path = xpr_path.replace('\\', '/')
	zip_path = zip_path.replace('\\', '/')
	
	if xpr_path[:-3] != '.xpr':
		print('Error: xpr_path argument must end in .xpr')
		sys.exit()
		
	if not accept_warning('If %s exists, it will be overwritten. Do you wish to continue?' % zip_path):
		sys.exit()
	
	print('Creating release %s from project %s' % (os.path.basename(zip_path), os.path.basename(xpr_path)))
	
	if DEBUG_NO_VIVADO:
		print ('vivado_cmd: %s' % vivado_cmd)
		print ('script_path: %s' % script_path)
		print ('xpr_path: %s' % xpr_path)
		print ('zip_path: %s' % zip_path)
	else:
		os.system("%s -mode batch -source %s -notrace -tclargs %s %s" % (vivado_cmd, script_path, xpr_path, zip_path))
	
# Parse CONFIG.INI
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
config = configparser.ConfigParser()
config.read("%s\config.ini" % script_dir)
default_repo_path = os.path.abspath(os.path.join(script_dir, '..'))

# Parse SYS.ARGV
parser = argparse.ArgumentParser(description='Handles vivado project git repo operations')
subparsers = parser.add_subparsers(help='sub-command help')

# Checkin Arguments
parser_checkin = subparsers.add_parser('checkin', help='Checks in XPR to REPO')
parser_checkin.set_defaults(func=do_checkin)
# Required Args
# Optional Args
parser_checkin.add_argument('-xpr', dest='xpr_path', type=str, default='none', help='Path to XPR file from %s' % (config['DEFAULT']['ProjectBasePath']))
parser_checkin.add_argument('-repo', dest='repo_path', type=str, default=default_repo_path, help='Path to target repository from %s/ - default assumes this script is in a submodule underneath the target repo' % (config['DEFAULT']['GithubBasePath']))
parser_checkin.add_argument('-v', dest='version', type=str, default='none', help='Vivado version number 20##.# - used to construct absolute path to vivado command. default uses \'vivado\'')

# Checkout Arguments
parser_checkout = subparsers.add_parser('checkout', help='Checks out XPR from REPO')
parser_checkout.set_defaults(func=do_checkout)
# Required Args
# Optional Args
parser_checkout.add_argument('-xpr', dest='xpr_path', type=str, default='none', help='Path to XPR file from %s - default assumes this script is in a submodule underneath the target repo' % (config['DEFAULT']['ProjectBasePath']))
parser_checkout.add_argument('-repo', dest='repo_path', type=str, default=default_repo_path, help='Path to target repository from %s/ - default assumes this script is in a submodule underneath the target repo' % (config['DEFAULT']['GithubBasePath']))
parser_checkout.add_argument('-v', dest='version', type=str, default='none', help='Vivado version number 20##.# - used to construct absolute path to vivado command. default uses \'vivado\'')

# Release Arguments
parser_release = subparsers.add_parser('release', help='Creates release ZIP from XPR')
parser_release.set_defaults(func=do_release)
# Required Args
parser_release.add_argument('zip_path', metavar='zip_path', type=str, help='Location and name to give release archive ZIP file')
# Optional Args
parser_release.add_argument('-xpr', dest='xpr_path', type=str, help='Path to XPR file from %s' % (config['DEFAULT']['ProjectBasePath']))
parser_release.add_argument('-v', dest='version', type=str, default='none', help='Vivado version number 20##.# - used to construct absolute path to vivado command. default uses \'vivado\'')

# Parse Arguments
args = parser.parse_args()

# Call selected function
try:
	args.func(script_dir, config, args)
except AttributeError:
	print("Please select a subcommand to execute. For a list of subcommands, use 'python3 %s --help'" % sys.argv[0])
