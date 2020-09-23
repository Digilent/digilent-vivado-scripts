# This is an automatically generated file used by digilent_vivado_checkout.tcl to set project options
proc set_project_properties_post_create_project {proj_name} {
    set project_obj [get_projects $proj_name]
    set_property "part" "<part>" $project_obj
    set_property "board_part" "<board_part>" $project_obj
    set_property "default_lib" "<default_lib>" $project_obj
    set_property "simulator_language" "<simulator_language>" $project_obj
    set_property "target_language" "<target_language>" $project_obj
}

proc set_project_properties_pre_add_repo {proj_name} {
    set project_obj [get_projects $proj_name]
    # default nothing
}

proc set_project_properties_post_create_runs {proj_name} {
    set project_obj [get_projects $proj_name]
	<directives>
}
