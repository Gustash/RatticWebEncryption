var $input = $("#input-0");
var $uploaded_notice = $("#uploaded-notice")
var rsa_key = Cookies.get('rsa_key');
console.log(rsa_key);
var csrftoken = Cookies.get('csrftoken');

if (rsa_key == null) {
	$input.show();
	$input.fileinput({
		uploadExtraData: {
			csrfmiddlewaretoken: csrftoken,
			returnUrl: window.location.href},
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

	$input.on('filebatchuploadsuccess', function(event, data, previewId, index) {
		console.log(data.extra.returnUrl);
		window.location.href = data.extra.returnUrl;
	});
} else {
	$uploaded_notice.show()
}
