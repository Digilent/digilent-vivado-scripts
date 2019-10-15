
# components of a release:
    # zip_file = <repo name>-<major version>-<minor version>.zip
        # sdk_workspace
            # contains hw, bsps, and apps, in source-control style
        # vivado_proj
            # collected through TCL archive_project
        # README.md

# Process:
# 1. archive project into repo/release/temp (in Vivado batch mode, source vivado_release_project.tcl)
# 2. copy workspace into repo/release/temp/sdk_workspace (in XSCT, source sdk_release_workspace.tcl)
# 3. extract archived project into repo/release/temp/vivado_proj
# 4. copy readme into repo/release/temp
# 5. zip repo/release/temp into repo/release/zip_file
# 6. delete temporary files (TODO)

import os
from glob import glob
from zipfile import ZipFile,ZIP_DEFLATED
from shutil import copyfile, copytree

def step_1(args):
    DEBUG_VIVADO_TCL_TRACE = args['DEBUG_VIVADO_TCL_TRACE']
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    
    
    vivado_cmd  = args['vivado_cmd'].replace('\\', '/')
    script_path = os.path.join(args['script_dir'], 'digilent_vivado_release.tcl').replace('\\', '/')
    repo_path = args['repo_path'].replace('\\', '/')
    zip_path = args['zip_path'].replace('\\', '/')
    temp_directory = args['temp_directory'].replace('\\', '/')
    xpr_path = args['xpr_path'].replace('\\', '/')
    notrace = '' if DEBUG_VIVADO_TCL_TRACE else ' -notrace'
    
    cmd = "%s -mode batch -source %s%s -tclargs -r %s -x %s -o %s -temp %s" % (
        vivado_cmd,
        script_path,
        notrace,
        # arguments:
        repo_path,
        xpr_path,
        zip_path,
        temp_directory
    )
    if DEBUG_NO_VIVADO:
        print(cmd)
    else:
        os.system(cmd)

    if not os.path.exists(zip_path):
        print('ERROR: archive not created')
        return None
    else:
        return zip_path

def step_2(args):
    DEBUG_NO_VIVADO = args['DEBUG_NO_VIVADO']
    repo_path = args['repo_path'].replace('\\', '/')
    xsct_cmd = args['xsct_cmd'].replace('\\', '/')
    script_path = os.path.join(args['script_dir'], 'digilent_sdk_release.tcl').replace('\\', '/')
    workspace = args['workspace'].replace('\\', '/')
    temp_directory = args['temp_directory'].replace('\\', '/')
    temp_workspace = os.path.join(temp_directory, "sdk_workspace").replace('\\', '/')
    
    cmd = "%s %s -r %s -ws %s -o %s" % (
        xsct_cmd,
        script_path,
        # arguments:
        repo_path,
        workspace,
        temp_workspace
    )
    print(cmd)
    if not DEBUG_NO_VIVADO:
        os.system(cmd)

    return temp_workspace

def step_3(args, vivado_archive):
    #major_version = args['version']
    repo_path = args['repo_path']
    repo_name = os.path.basename(repo_path)
    #minor_version = '1'
    temp_dir = args['temp_directory']
    
    if not os.path.exists(vivado_archive):
        print("ERROR: vivado archive not found")
        return None
    
    with ZipFile(vivado_archive, 'r') as zip_object:
        zip_object.extractall(temp_dir)
        # TODO: ignore vivado_proj/*.sdk directory and contents
    os.remove(vivado_archive)
    os.rename(os.path.join(temp_dir, repo_name), os.path.join(temp_dir, 'vivado_proj'))

def step_4(args):
    repo_path = args['repo_path']
    temp_dir = args['temp_directory']
    copyfile(os.path.join(repo_path, 'README.md'), os.path.join(temp_dir, 'README.md'))

def step_5(args):
    zip_path = args['zip_path']
    temp_dir = args['temp_directory']
    zip_object = ZipFile(zip_path, 'w', ZIP_DEFLATED)
    for root, unused_dirs, files in os.walk(temp_dir):
        for file_object in files:
            file_path = os.path.join(root, file_object)
            file_relpath = os.path.relpath(file_path, os.path.join(temp_dir, '..'))
            zip_object.write(file_path, file_relpath)
    zip_object.close()

def step_6(args):
    # TODO: implement cleanup operation
    return

def do_release(args):
    print("Release Step 1. archive project into %s (in Vivado batch mode, source vivado_release_project.tcl)" % (args['temp_directory']))
    vivado_archive = step_1(args)
    print("Release Step 2. copy workspace into %s (in XSCT, source sdk_release_workspace.tcl)" % (os.path.join(args['temp_directory'], "sdk_workspace")))
    step_2(args)
    print("Release Step 3. extract archived project into %s" % (args['temp_directory']))
    step_3(args, vivado_archive)
    print("Release Step 4. copy readme into %s" % (args['temp_directory']))
    step_4(args)
    print("Release Step 5. zip %s into %s" % (args['temp_directory'], args["zip_path"]))
    step_5(args)
    print("Release Step 6. delete temporary files (TODO)")
    step_6(args)