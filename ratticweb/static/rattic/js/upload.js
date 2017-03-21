var $input = $("#input-0");
console.log($input);
$input.fileinput({
	uploadUrl: "#",
	uploadAsync: false,
	showUpload: false,
	showRemove: false,
	showPreview: false,
	showCaption: false,
	minFileCount: 1,
	maxFileCount: 1,
}).on("filebatchselected", function(event, files) {
	$input.fileinput("upload");
});
