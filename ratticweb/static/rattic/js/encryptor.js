$('#cred-edit-form').submit(function(e) {
	if (!($('#id_group').val())) {
		if (getKeyValue() !== null) {
		raw_password = $('#id_password').val();
		var privateKey = getPrivateKey();	
		var publicKey = getPublicKey(privateKey);
		var utf8 = forge.util.encodeUtf8(raw_password);
		var ciphertext = forge.util.encode64(publicKey.encrypt(utf8));
		$('#id_password').val(ciphertext);
		} else {
			console.log('No key loaded');
			e.preventDefault();
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

function getPrivateKey() {
	return forge.pki.privateKeyFromPem(getKeyValue());
};

function getPublicKey(privateKey) {
	return forge.pki.setRsaPublicKey(privateKey.n, privateKey.e);
};
