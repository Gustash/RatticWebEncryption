var $input = $("#input-0");
var $uploaded_notice = $("#uploaded-notice");
var $remove_anchor = $("#delete-cookie-anchor");
var rsa_key = Cookies.get('rsa_key');

if (rsa_key == null) {
	$input.show();
	$input.fileinput({
		showUpload: false,
		showRemove: false,
		showPreview: false,
		showCaption: false,
		minFileCount: 1,
		maxFileCount: 1,
	}).on("filebatchselected", function(event, files) {
		var reader = new FileReader();

		reader.onload = function (e) {
			saveCookie(e.target.result);
			window.location.href = window.location.href;
		}
		reader.readAsText(files[0]);

	});
} else {
	$uploaded_notice.show();
	$remove_anchor.click(function() {
		deleteCookie();
		window.location.href = window.location.href;
	});
}

function saveCookie(key) {
	var inThreeHours = new Date(new Date().getTime() + 3 * 60 * 60 * 1000);
	Cookies.set('rsa_key', key, { expires: inThreeHours });
}

function deleteCookie() {
	Cookies.remove('rsa_key')
}
