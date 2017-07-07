$(document).ready(function() {
	is_add = (window.location.pathname.split('/')[2] === "add");
	cant_be_private = false;
	if (!is_add) {
		if ($('#group_selector').is('select')) {
			if ($('#group_selector').find(':selected').val() !== '') {
				console.log('I am here');
				cant_be_private = true;	
			}
		}
	}	
});

$('#cred-edit-form').submit(function(e) {
	if ($('#group_selector').is('select')) {
		if ($('#group_selector').find(':selected').val() === '') {
			if (!cant_be_private) {
				if ($('#id_groups').find(':selected').length === 0) {
					// This is a private password. Encrypt server side.	
					if (getKeyValue() !== null) {
						raw_password = $('#id_password').val();
						var privateKey = getPrivateKey();	
						var publicKey = getPublicKey(privateKey);
						var utf8 = forge.util.encodeUtf8(raw_password);
						var ciphertext = forge.util.encode64(publicKey.encrypt(utf8));
						$('#id_password').val(ciphertext);
					} else {
						console.log('No key loaded');
						alert('You need to load a PEM encryption key file in order to create private passwords.');
						e.preventDefault();
					}
				} else {
					alert('A private password can\'t have Viewer Groups. Either select an Owner Group or remove the Viewer Groups.');
					e.preventDefault();
				}
			 } else {
				// The user is editting a group password. It can't be private.
				alert('The password you\'re editting is in a group. You need to select a group.');
				e.preventDefault();
			 }
		}
	}

//	console.log('Canceling POST');
//	e.preventDefault();
});

if ($('#password').is('span')) {
	try {
		var encryptedPassword = $('#password').text();
		var privateKey = getPrivateKey();
		var decrypted = privateKey.decrypt(forge.util.decode64(encryptedPassword));
		var plaintext = forge.util.decodeUtf8(decrypted);
		$('#password').text(plaintext);
	} catch (err) {
		console.log(err.message);
		if (err.message === "Invalid PEM formatted message.") {
			// No key was loaded. Check if that was the case.
			// But first check if the password is just a group one.
			if ($('#owner-group-id').text().startsWith("private_")) {
				// This is a private key. Warn user they have no key.
				if (getKeyValue() === null) {
					alert("No PEM encryption key was loaded.");
					window.location.href = '/cred/list/';
				}
			}
		} else if (err.message === "Encrypted message length is invalid.") {
			// This is a group pass. Do nothing.
		} else if (err.message === "Encryption block is invalid.") {
			// The wrong key was used to decrypt. Warn user.
			alert("The PEM encryption key provided is not the same that was used to encrypt this password."); 
			window.location.href = '/cred/list/';
		}
	}
};

if ($('#id_password').is('input')) {
	try {
		var encryptedPassword = $('#id_password').val();
		var privateKey = getPrivateKey();
		var decrypted = privateKey.decrypt(forge.util.decode64(encryptedPassword));
		var plaintext = forge.util.decodeUtf8(decrypted);
		$('#id_password').val(plaintext);
	} catch (err) {
		console.log(err.message);
		if (err.message === "Invalid PEM formatted message.") {
			// No key was loaded. Check if that was the case.
			// But first check if the password is just a group one.
			if ($('#owner-group-id').is('td')) {
				if ($('#owner-group-id').text().startsWith("private_")) {
					// This is a private key. Warn user they have no key.
					if (getKeyValue() === null) {
						alert("No PEM encryption key was loaded.");
						window.location.href = '/cred/list/';
					}
				}
			} else if ($('#group_selector').is('select')) {
				// The user is editing an existing cred. Check if it is a group one or not.
				console.log($('#group_selector').find(':selected').val() === '');
				if ($('#id_password').val() !== '' && $('#group_selector').find(':selected').val() === '') {
					if (getKeyValue() === null) {
						alert("No PEM encryption key was loaded.");
						window.location.href = '/cred/list/';
					}
				}
			}	
		} else if (err.message === "Encrypted message length is invalid.") {
			// This is a group pass. Do nothing.
		} else if (err.message === "Encryption block is invalid.") {
			// The wrong key was used to decrypt. Warn user.
			alert("The PEM encryption key provided is not the same that was used to encrypt this password."); 
			window.location.href = '/cred/list/';
		}
	}
}

function getPrivateKey() {
	return forge.pki.privateKeyFromPem(getKeyValue());
};

function getPublicKey(privateKey) {
	return forge.pki.setRsaPublicKey(privateKey.n, privateKey.e);
};
