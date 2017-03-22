$('#cred-edit-form').submit(function(e) {
	if (!($('#id_group').val())) {
		raw_password = $('#id_password').val();
		var privateKey = getPrivateKey();	
		var publicKey = getPublicKey(privateKey);
		var utf8 = forge.util.encodeUtf8(raw_password);
		var ciphertext = forge.util.encode64(publicKey.encrypt(utf8));
		$('#id_password').val(ciphertext);
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
		// Not a private password. Do nothing.
	}
};

function getPrivateKey() {
	return forge.pki.privateKeyFromPem(getKeyValue());
};

function getPublicKey(privateKey) {
	return forge.pki.setRsaPublicKey(privateKey.n, privateKey.e);
};
