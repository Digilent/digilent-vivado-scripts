# checkin.tcl
#
# Write the sources of an existing Vivado project to the repository.
# Existing files are updated, files no longer in the project are removed.
#
# Usage (argument order does not matter, all are optional):
#   set argv "-r <repo_path> -x <xpr_path> -v <version>"
#   source checkin.tcl
#
# Arguments:
#   -r  repo, default is the parent of the scripts directory
#   -x  project file, default is the only .xpr in <repo>/proj
#   -v  Vivado version, default is the running one


# Helpers

# Return the value following flag in argv, or default when flag is absent
proc arg_value {flag default} {
    global argv
    set idx [lsearch ${argv} ${flag}]
    if {${idx} == -1} {
        return ${default}
    }
    return [lindex ${argv} [expr {${idx}+1}]]
}

# Copy origin to target, updating the target when it already exists
proc save_file {origin target} {
    if {[file normalize ${origin}] eq [file normalize ${target}]} {
        return
    }
    file copy -force ${origin} ${target}
}

# Delete everything in dir that is not in keep, the .keep files stay
proc remove_stale {dir keep} {
    foreach entry [glob -nocomplain -directory ${dir} -types {f d} *] {
        if {[lsearch -exact ${keep} [file normalize ${entry}]] == -1} {
            puts "INFO: Removing [file tail ${entry}] from version control."
            file delete -force ${entry}
        }
    }
}


# Arguments

set script_dir [file normalize [file dirname [info script]]]

set repo_path [glob -nocomplain [file normalize [arg_value "-r" "${script_dir}/.."]]]

set xpr_path [glob -nocomplain [file normalize [arg_value "-x" "${repo_path}/proj/*.xpr"]]]
if {[llength ${xpr_path}] != 1} {
    error "XPR not found"
}
set xpr_path [lindex ${xpr_path} 0]

set vivado_version [arg_value "-v" [version -short]]

# Included for possible argument support in future
set force_overwrite_info_script 0

set proj_file [file tail ${xpr_path}]
set proj_dir [file dirname ${xpr_path}]
set proj_name [file rootname ${proj_file}]


# Open the project

puts "INFO: Checking project \"${proj_file}\" into version control."
set already_opened [get_projects -filter "DIRECTORY==${proj_dir} && NAME==${proj_name}"]
if {[llength ${already_opened}] == 0} {
    open_project ${xpr_path}
} else {
    current_project [lindex ${already_opened} 0]
}


# Repository layout

set required_dirs [list                 \
    ${repo_path}/proj                   \
    ${repo_path}/hw_handoff             \
    ${repo_path}/src                    \
    ${repo_path}/src/bd                 \
    ${repo_path}/src/constraints        \
    ${repo_path}/src/ip                 \
    ${repo_path}/src/hdl                \
    ${repo_path}/src/other              \
    ${repo_path}/repo                   \
    ${repo_path}/repo/local             \
]
set required_files [list                \
    ${repo_path}/proj/.keep             \
    ${repo_path}/hw_handoff/.keep       \
    ${repo_path}/src/bd/.keep           \
    ${repo_path}/src/constraints/.keep  \
    ${repo_path}/src/ip/.keep           \
    ${repo_path}/src/hdl/.keep          \
    ${repo_path}/src/other/.keep        \
    ${repo_path}/repo/local/.keep       \
]

# Create any missing directories and .keep files
foreach d ${required_dirs} {
    if {![file exists ${d}]} {
        file mkdir ${d}
    }
}
foreach f ${required_files} {
    if {![file exists ${f}]} {
        close [open ${f} "w"]
    }
}

# Targets written below, anything else in these directories is stale
set kept_hdl   [list [file normalize ${repo_path}/src/hdl/.keep]]
set kept_other [list [file normalize ${repo_path}/src/other/.keep]]
set kept_ip    [list [file normalize ${repo_path}/src/ip/.keep]]
set kept_xdc   [list [file normalize ${repo_path}/src/constraints/.keep]]


# Block design

set bd_files [get_files -filter "NAME=~*.bd && NAME!~*/bd/*/ip/*"]
if {[llength ${bd_files}] > 1} {
    error "This script cannot handle projects containing more than one block design!"
}
set has_bd [expr {[llength ${bd_files}] == 1}]
if {${has_bd}} {
    set bd_file [lindex ${bd_files} 0]
    open_bd_design ${bd_file}
    set bd_name [file tail [file rootname [get_property NAME ${bd_file}]]]
    set script_name "${repo_path}/src/bd/${bd_name}.tcl"
    puts "INFO: Checking in ${script_name} to version control."
    write_bd_tcl -force -no_ip_version -make_local ${script_name}
}


# HDL and other sources
# Files generated inside the project directory or an IP directory are skipped

foreach source_file [get_files -of_objects [get_filesets sources_1]] {
    set origin [get_property name ${source_file}]
    set skip 0
    if {[lsearch -exact {.vhd .v .sv} [file extension ${origin}]] != -1} {
        set subdir hdl
    } elseif {[lsearch -exact {.bd .xci .xcix} [file extension ${origin}]] == -1} {
        set subdir other
    } else {
        set skip 1
    }

    if {[string first "[file normalize ${proj_dir}]/" [file normalize ${origin}]] == 0} {
        set skip 1
    }
    foreach ip [get_ips] {
        set ip_dir [get_property IP_DIR ${ip}]
        set source_length [string length ${source_file}]
        set dir_length [string length ${ip_dir}]
        if {${source_length} >= ${dir_length}
                && [string range ${source_file} 0 ${dir_length}-1] == ${ip_dir}} {
            set skip 1
        }
    }

    if {!${skip}} {
        puts "INFO: Checking in [file tail ${origin}] to version control."
        set target ${repo_path}/src/${subdir}/[file tail ${origin}]
        save_file ${origin} ${target}
        lappend kept_${subdir} [file normalize ${target}]
    }
}
remove_stale ${repo_path}/src/hdl ${kept_hdl}
remove_stale ${repo_path}/src/other ${kept_other}


# IP
# Block design projects keep their IP in the block design script

if {!${has_bd}} {
    # Convert each core container back to its original format
    foreach ip [get_ips] {
        set ip_core_cont [get_property IP_CORE_CONTAINER ${ip}]
        if {[llength ${ip_core_cont}] != 0} {
            puts "INFO: Found ${ip_core_cont} for ${ip}"
            puts "Convert ${ip} from the core container format to the expanded format"
            convert_ips -force -from_core_container [get_files [get_property ip_file ${ip}]]
        }
    }

    foreach ip [get_ips] {
        set origin [get_property ip_file ${ip}]
        set ipname [get_property name ${ip}]
        set dir "${repo_path}/src/ip/${ipname}"
        if {![file exists ${dir}]} {
            file mkdir ${dir}
        }
        set target ${dir}/[file tail ${origin}]
        puts "INFO: Checking in [file tail ${origin}] to version control."
        save_file ${origin} ${target}
        lappend kept_ip [file normalize ${dir}] [file normalize ${target}]
    }

    remove_stale ${repo_path}/src/ip ${kept_ip}
}


# Constraints

foreach constraint_file [get_files -of_objects [get_filesets constrs_1]] {
    set origin [get_property name ${constraint_file}]
    set target ${repo_path}/src/constraints/[file tail ${origin}]
    puts "INFO: Checking in [file tail ${origin}] to version control."
    save_file ${origin} ${target}
    lappend kept_xdc [file normalize ${target}]
}
remove_stale ${repo_path}/src/constraints ${kept_xdc}


# project_info.tcl
# Created only when missing (first checkin, or deleted by the user).

if {![file exists ${repo_path}/project_info.tcl] || ${force_overwrite_info_script} != 0} {
    set proj_obj [get_projects ${proj_name}]

    set board_part [current_board_part -quiet]
    set part [get_property part ${proj_obj}]
    set default_lib [get_property default_lib ${proj_obj}]
    set simulator_language [get_property simulator_language ${proj_obj}]
    set target_language [get_property target_language ${proj_obj}]
    set directives "#Custom directives for synthesis and implementation"

    # Fetch the non-default synthesis and implementation settings
    foreach run_name {synth_1 impl_1} {
        foreach prop [list_property [get_runs ${run_name}] STEPS.*.ARGS.*] {
            set Dval [list_property_value -default ${prop} [get_runs ${run_name}]]
            set val [get_property ${prop} [get_runs ${run_name}]]
            if {${Dval} != ${val}} {
                append directives "\n\tset_property " ${prop} " " ${val} " \[get_runs ${run_name}\]"
            }
        }
    }

    puts "INFO: Checking in project_info.tcl to version control."

    set var_map [list <part> ${part}                             \
                      <default_lib> ${default_lib}               \
                      <simulator_language> ${simulator_language} \
                      <target_language> ${target_language}       \
                      <directives> ${directives}                 \
    ]

    # Replace even an empty board_part, or the placeholder is read as a board name on checkout
    lappend var_map <board_part> ${board_part}

    set dfid [open ${repo_path}/project_info.tcl "w"]
    set sfid [open ${script_dir}/templates/project_info.tcl "r"]
    while {[gets ${sfid} line] >= 0} {
        puts ${dfid} [string map ${var_map} ${line}]
    }
    close ${dfid}
    close ${sfid}
}


# Repository files

set post_build_script [file join ${repo_path} post_build.tcl]
if {![file exists ${post_build_script}]} {
    puts "WARNING: This repository does not contain a post_build script. Creating one now."
    file copy -force [file join ${script_dir} templates post_build.tcl] ${post_build_script}
}

set master_gitignore [file join ${repo_path} .gitignore]
if {![file exists ${master_gitignore}]} {
    puts "WARNING: This repository does not contain a master gitignore. Creating one now."
    file copy -force ${script_dir}/templates/hw.gitignore ${master_gitignore}
}

puts "INFO: Project ${proj_file} has been checked into version control"
