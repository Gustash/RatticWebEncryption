$(document).ready(function() {
	var group_input = $("div.control-group").find("div.controls").find("input#id_group");
	var groups_input = $("div.control-group").find("div.controls").find("input#id_groups");

	var is_group_visible = group_input.is(":visible");
	var is_groups_visible = groups_input.is(":visible");

	if (!is_group_visible) {
		group_input.parent().parent().hide();
	}

	if (!is_groups_visible) {
		groups_input.parent().parent().hide();
	}
});
