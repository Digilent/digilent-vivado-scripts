# checkout.tcl
#
# Recreate the Vivado project from the sources of the repository,
# optionally building it.
#
# Usage (argument order does not matter, all are optional):
#   set argv "-r <repo_path> -x <xpr_path> -v <version> -b -no-block \
#             -ip-cache <dir> -D <NAME> <VALUE>"
#   source checkout.tcl
#
# Arguments:
#   -r         repo, default is the parent of the scripts directory
#   -x         project file, default is <repo>/proj/<repo name>.xpr
#   -v         Vivado version, default is the running one
#   -b         build the project after checkout
#   -no-block  with -b, do not wait for the build to finish
#   -ip-cache  IP output repository, default is <repo>/proj/cache;
#              use one per project when checking out in parallel
#   -D         set a global Tcl variable for the block design script,
#              repeatable, NAME and VALUE are two separate tokens
#              (vivado.bat splits "NAME=VALUE" on "=")


# Helpers

# Return 1 when flag is present in argv
proc arg_present {flag} {
    global argv
    return [expr {[lsearch ${argv} ${flag}] != -1}]
}

# Return the value following flag in argv, or default when flag is absent
proc arg_value {flag default} {
    global argv
    set idx [lsearch ${argv} ${flag}]
    if {${idx} == -1} {
        return ${default}
    }
    return [lindex ${argv} [expr {${idx}+1}]]
}


# Arguments

if {[arg_present "-r"]} {
    set repo_path [glob -nocomplain [file normalize [arg_value "-r" ""]]]
} else {
    set repo_path [file normalize [file dirname [info script]]/..]
}

if {[arg_present "-x"]} {
    set xpr_path [file normalize [arg_value "-x" ""]]
} else {
    set xpr_path [file join ${repo_path} proj [file tail $repo_path]].xpr
}

if {[arg_present "-v"]} {
    set vivado_version [arg_value "-v" ""]
} else {
    set vivado_version [version -short]
}

set build_when_checked_out [arg_present "-b"]
set wait_on_build [expr {![arg_present "-no-block"]}]

if {[arg_present "-ip-cache"]} {
    set ip_cache_dir [file normalize [arg_value "-ip-cache" ""]]
} else {
    set ip_cache_dir [file normalize "$repo_path/proj/cache"]
}

# Set the -D variables before the block design script is sourced, so it can
# switch build-time options with [info exists ::NAME]
set idx 0
while {[set idx [lsearch -start $idx ${argv} "-D"]] != -1} {
    set define_name [lindex ${argv} [expr {${idx}+1}]]
    set define_value [lindex ${argv} [expr {${idx}+2}]]
    if {${define_name} eq ""} {
        puts "WARNING: Ignoring malformed -D argument (expected -D NAME VALUE) at argv index $idx"
        incr idx
    } else {
        set ::${define_name} ${define_value}
        puts "INFO: Set global Tcl variable $define_name = $define_value (via -D)"
        incr idx 3
    }
}

set vivado_year [lindex [split $vivado_version "."] 0]
set proj_name [file rootname [file tail $xpr_path]]


# Project

puts "INFO: Creating new project \"$proj_name\" in [file dirname $xpr_path]"
create_project $proj_name [file dirname $xpr_path]

source $repo_path/project_info.tcl

puts "INFO: Capturing board information from $repo_path/project_info.tcl"
set_project_properties_post_create_project $proj_name
set obj [get_projects $proj_name]
set part_name [get_property "part" $obj]

# Faster builds with IPs and block designs
puts "INFO: Configuring project IP handling properties"
set_property "corecontainer.enable" "0" $obj
set_property "ip_cache_permissions" "read write" $obj
# The cache is shared by all checkouts of this repo, which speeds up the next
# one, but only one checkout at a time may populate it
puts "INFO: Using IP cache directory $ip_cache_dir"
set_property "ip_output_repo" $ip_cache_dir $obj

if {[string equal [get_filesets -quiet sources_1] ""]} {
    puts "INFO: Creating sources_1 fileset"
    create_fileset -srcset sources_1
}

if {[string equal [get_filesets -quiet constrs_1] ""]} {
    puts "INFO: Creating constrs_1 fileset"
    create_fileset -constrset constrs_1
}

puts "INFO: capturing IP-related settings from $repo_path/project_info.tcl"
set_project_properties_pre_add_repo $proj_name


# Sources

puts "INFO: Setting IP repository paths"
set obj [get_filesets sources_1]
set_property "ip_repo_paths" "[file normalize $repo_path/repo]" $obj

puts "INFO: Refreshing IP repositories"
update_ip_catalog -rebuild

puts "INFO: Adding HDL sources"
add_files -quiet -norecurse [glob -nocomplain $repo_path/src/hdl/*.v]
add_files -quiet -norecurse [glob -nocomplain $repo_path/src/hdl/*.vhd]
add_files -quiet -norecurse [glob -nocomplain $repo_path/src/hdl/*.sv]

puts "INFO: Adding XCI IP sources"
add_files -quiet [glob -nocomplain $repo_path/src/ip/*/*.xci]
add_files -quiet [glob -nocomplain $repo_path/src/ip/*/*.xcix]

puts "INFO: Adding constraints"
add_files -quiet -norecurse -fileset constrs_1 [glob -nocomplain $repo_path/src/constraints/*.xdc]


# Block design

# Only one block design is supported, more than one is an error
set ipi_tcl_files [glob -nocomplain "$repo_path/src/bd/*.tcl"]
set ipi_bd_files [glob -nocomplain "$repo_path/src/bd/*/*.bd"]
if {[llength $ipi_tcl_files] > 1} {
    error "This script cannot handle projects containing more than one block design! More than one tcl script found in src/bd"
} elseif {[llength $ipi_tcl_files] == 1} {
    puts "INFO: Rebuilding block design from script"
    set srcs_dir "[file rootname $xpr_path].srcs"
    file mkdir "$srcs_dir/sources_1/bd"

    # The script must run from sources_1, with the remote bd flow off
    set origin_dir [pwd]
    cd "$srcs_dir/sources_1"
    set run_remote_bd_flow 0
    if {[set result [catch { source [lindex $ipi_tcl_files 0] } resulttext]]} {
        # Keep the error state of the script, but restore the directory first
        set einfo $::errorInfo
        set ecode $::errorCode
        catch {cd $origin_dir}
        return -code $result -errorcode $ecode -errorinfo $einfo $resulttext
    }
    cd $origin_dir
} elseif {[llength $ipi_bd_files] > 1} {
    error "This script cannot handle projects containing more than one block design! More than one bd file found in src/bd"
} elseif {[llength $ipi_bd_files] == 1} {
    puts "INFO: Rebuilding block design from BD fileset"
    add_files -norecurse -quiet -fileset sources_1 [glob -nocomplain $repo_path/src/bd/*/*.bd]
    open_bd_design [glob -nocomplain $repo_path/src/bd/*/*.bd]
    set design_name [get_bd_designs]
    set file "$repo_path/src/bd/$design_name/$design_name.bd"
    set file [file normalize $file]
    set file_obj [get_files -of_objects [get_filesets sources_1] [list "*$file"]]
    if { ![get_property "is_locked" $file_obj] } {
        set_property "synth_checkpoint_mode" "Hierarchical" $file_obj
    }
}

# Upgrade the locked IPs to the most recent version
foreach ip [get_ips -filter "IS_LOCKED==1"] {
    upgrade_ip -vlnv [get_property UPGRADE_VERSIONS $ip] $ip
    export_ip_user_files -of_objects $ip -no_script -sync -force -quiet
}

# Generate the wrapper of the root design, the catch skips projects without a
# block design
catch {
    set bd_name [get_bd_designs -of_objects [get_bd_cells /]]
    set bd_file [get_files $bd_name.bd]
    set wrapper_file [make_wrapper -files $bd_file -top -force]
    import_files -quiet -force -norecurse $wrapper_file

    set obj [get_filesets sources_1]
    set_property "top" "${bd_name}_wrapper" $obj
}


# Runs

if {[string equal [get_runs -quiet synth_1] ""]} {
    puts "INFO: Creating synth_1 run"
    create_run -name synth_1 -part $part_name -flow "Vivado Synthesis $vivado_year" -strategy "Vivado Synthesis Defaults" -constrset constrs_1
} else {
    set_property strategy "Vivado Synthesis Defaults" [get_runs synth_1]
    set_property flow "Vivado Synthesis $vivado_year" [get_runs synth_1]
}
puts "INFO: Configuring synth_1 run"
set obj [get_runs synth_1]
set_property "part" $part_name $obj

puts "INFO: Setting current synthesis run"
current_run -synthesis [get_runs synth_1]

if {[string equal [get_runs -quiet impl_1] ""]} {
    puts "INFO: Creating impl_1 run"
    create_run -name impl_1 -part $part_name -flow "Vivado Implementation $vivado_year" -strategy "Vivado Implementation Defaults" -constrset constrs_1 -parent_run synth_1
} else {
    set_property strategy "Vivado Implementation Defaults" [get_runs impl_1]
    set_property flow "Vivado Implementation $vivado_year" [get_runs impl_1]
}
puts "INFO: Configuring impl_1 run"
set obj [get_runs impl_1]
set_property "part" $part_name $obj

puts "INFO: Setting current implementation run"
current_run -implementation [get_runs impl_1]

puts "INFO: capturing run settings from $repo_path/project_info.tcl"
set_project_properties_post_create_runs $proj_name


# Simulation

# One simulation set per folder in src/sim, the top is the file named *_tb
set sim_dirs [glob -nocomplain -type d $repo_path/src/sim/*]
foreach sim_dir $sim_dirs {
    set sim_name [file tail $sim_dir]
    # sim_1 already exists in a fresh project, creating it again is an error
    if {[get_fileset $sim_name] == ""} {
        puts "INFO: Simulation set $sim_name does not exist, creating it"
        create_fileset -simset $sim_name
    }
    set_property SOURCE_SET sources_1 [get_filesets $sim_name]
    set top_found 0
    foreach source_file [glob -nocomplain -type f $sim_dir/*] {
        add_files -quiet -fileset $sim_name -norecurse $source_file
        set module_name [file tail [file rootname $source_file]]
        puts "INFO: Imported $source_file for $sim_name"
        if {[string range $module_name end-2 end] == "_tb"} {
            update_compile_order -fileset $sim_name
            set_property top $module_name [get_filesets $sim_name]
            puts "INFO: Picked $module_name as top-level testbench for $sim_name"
            set top_found 1
        }
    }
    if {$top_found == 0} {
        puts "WARNING: No testbench (identified by suffix _tb) found in simulation set $sim_name"
    }
    set_property top_lib xil_defaultlib [get_filesets $sim_name]
    update_compile_order -fileset $sim_name
}


# Build

set post_build_script [glob -nocomplain [file join ${repo_path} post_build.tcl]]

# Return the runs that failed at startup with "tclapp::load_apps failed".
# Concurrent vivado starts can clobber the per-user tclapp manifest, which is
# unrelated to the design, so those runs are safe to repeat.
proc startup_failed_runs {} {
    set failed [list]
    foreach r [get_runs] {
        if {[string match "*Complete*" [get_property STATUS ${r}]]} {
            continue
        }
        set log [file join [get_property DIRECTORY ${r}] runme.log]
        if {![file exists ${log}]} {
            continue
        }
        set fid [open ${log} r]
        set text [read ${fid}]
        close ${fid}
        if {[string first "tclapp::load_apps" ${text}] != -1} {
            lappend failed ${r}
        }
    }
    return ${failed}
}

# Build to the bitstream and wait, repeating once after a startup failure
proc build_and_wait {} {
    set attempt 1
    while {1} {
        launch_runs -to_step write_bitstream impl_1
        if {![catch {wait_on_run impl_1} err]} {
            return
        }
        set retry_runs [startup_failed_runs]
        if {${attempt} >= 2 || [llength ${retry_runs}] == 0} {
            error ${err}
        }
        puts "WARNING: Run(s) [join ${retry_runs} {, }] failed at startup, repeating them once"
        foreach r ${retry_runs} {
            reset_run ${r}
        }
        reset_run synth_1
        reset_run impl_1
        incr attempt
    }
}

if {${build_when_checked_out}} {
    if {${wait_on_build}} {
        build_and_wait
        puts "INFO: Build complete"

        # The post_build script can export the handoff and release files
        if {${post_build_script} ne ""} {
            source ${post_build_script}
        } else {
            puts "INFO: No post_build script found"
        }
    } else {
        launch_runs -to_step write_bitstream impl_1
        if {${post_build_script} ne ""} {
            puts "WARNING: Build launched but ${post_build_script} has not been run"
            puts "         After the bitstream has been generated, run the command 'source ${post_build_script}'"
        } else {
            puts "INFO: No post_build script found"
        }
    }
}

puts "INFO: Project created: [file tail $proj_name]"
puts "INFO: Exiting digilent_vivado_checkout"
