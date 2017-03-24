$(document).ready(function() {
	//var group_input = $("div.control-group").find("div.controls").find("input#id_group");
	//var groups_input = $("div.control-group").find("div.controls").find("input#id_groups");

	//var is_group_visible = group_input.css('display') !== 'none';
	//var is_groups_visible = groups_input.css('display') !== 'none';

	//if (!is_group_visible) {
	//	group_input.parent().parent().hide();
	//}

	//if (!is_groups_visible) {
	//	groups_input.parent().parent().hide();
	//}
	if($('#esconder_1').length){
		$('#esconder_1').parent().parent().hide();
	}

	if($('#esconder_2').length){
		$('#esconder_2').parent().parent().hide();
	}
});
