$('#cred-edit-form').submit(function(e) {
	raw_password = $('#id_password').val();

//	var keys = forge.pki.rsa.generateKeyPair(2048);
//	var pem = forge.pki.publicKeyToPem(keys.publicKey);
//	console.log(pem);
//	console.log(keys.publicKey);
	var privateKey = forge.pki.privateKeyFromPem(getKeyValue());
	var publicKey = forge.pki.setRsaPublicKey(privateKey.n, privateKey.e);

	var utf8 = forge.util.encodeUtf8(raw_password);
	var ciphertext = publicKey.encrypt(utf8);
	$('#id_password').val(ciphertext);

//	console.log('Canceling POST');
//	e.preventDefault();
});
