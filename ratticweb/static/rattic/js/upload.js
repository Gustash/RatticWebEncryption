var $input = $("#input-0");
console.log($input);

var csrftoken = Cookies.get('csrftoken');
console.log(csrftoken);

$input.fileinput({
	uploadExtraData: {csrfmiddlewaretoken: csrftoken},
	uploadUrl: "/account/upload/",
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
