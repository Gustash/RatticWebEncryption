var localStorageAvailable = false;

if (typeof(Storage) !== "undefined") {
	localStorageAvailable = true;
}

function saveCookie(key) {
	var inThreeHours = new Date(new Date().getTime() + 3 * 60 * 60 * 1000);
	Cookies.set('rsa_key', key, { expires: inThreeHours });
}

function deleteCookie() {
	Cookies.remove('rsa_key')
}

function saveKey(key) {
	var inThreeHours = new Date(new Date().getTime() + 3 * 60 * 60 * 1000);
	var keyToStore = {
		value: key,
		expires: inThreeHours
	};
	localStorage.setItem('rsa_key', JSON.stringify(keyToStore));
}

function getKeyValue() {
	if (localStorageAvailable) {
		if (localStorage.getItem('rsa_key') !== null) {
			var object = JSON.parse(localStorage.rsa_key);
			return object.value;
		};
	} else {
		if (Cookies.get('rsa_key') !== undefined) {
			return Cookies.get('rsa_key');
		}
	};
	return null;
}

function checkIfKeyIsExpired() {
	if (localStorage.getItem('rsa_key') !== null) {
		var object = JSON.parse(localStorage.rsa_key);
		var date = object.expires;

		if (date > (new Date().getTime())) {
			deleteKey();
		};
	};
}

function deleteKey() {
	localStorage.removeItem('rsa_key');
}

function keyIsValid(key) {
	try {
		forge.pki.privateKeyFromPem(key);
		return true;
	} catch (err) {
		return false;
	}
}

var $input = $("body [id='input-0']");
var $uploaded_notice = $("body [id='uploaded-notice']");
var $remove_anchor = $("body [id='delete-cookie-anchor']");
var $logout_button = $('#logout-button');
var rsa_key = getKeyValue();
checkIfKeyIsExpired();

console.log("ONE:" + $('body [id="input-0"]').length)
console.log("TWO:" + $('body [id="uploaded-notice"]').length)
console.log("THREE:" + $('body [id="delete-cookie-anchor"]').length)

$logout_button.click(function () {
	if (getKeyValue() !== null) {
		if (localStorageAvailable) {
			deleteKey();
		} else {
			deleteCookie();
		}
	}
});

if (rsa_key == null) {
	$input.each(
		function(){
			$(this).show();
		}
	)
	$input.each(function(){
		$(this).fileinput({
			showUpload: false,
			showRemove: false,
			showPreview: false,
			showCaption: false,
			minFileCount: 1,
			maxFileCount: 1,
		}).on("filebatchselected", function(event, files) {
			console.log(files);
			console.log(files[0].name.endsWith('.pem'));
			if (files[0].name.endsWith('.pem')) {
				var reader = new FileReader();

				reader.onload = function (e) {
					if (keyIsValid(e.target.result)) {
						if (localStorageAvailable) {
							saveKey(e.target.result);
						} else {
							saveCookie(e.target.result);
						}
						window.location.href = window.location.href;
					} else {
						alert('The provided PEM encryption key is not valid.');
					}
				}
				reader.readAsText(files[0]);
			} else {
				alert('The provided file is not a PEM encryption key.');
			}

		});
	});
} else {
	$uploaded_notice.each(
		function(){
			$(this).show();
		}
	)
	$remove_anchor.each(
		function(){
			$(this).click(function() {
			if (localStorageAvailable) {
				deleteKey();
			} else {
				deleteCookie();
			}
			window.location.href = window.location.href;
			});
		}
	)
}

