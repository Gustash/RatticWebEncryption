$('#key_generator').click
(
    function()
    {
        var keys = forge.pki.rsa.generateKeyPair(1024);
	pem = forge.pki.privateKeyToPem(keys.privateKey)	


	var keyLink = window.document.createElement('a');
	keyLink.href = window.URL.createObjectURL(new Blob([forge.pki.privateKeyToPem(keys.privateKey)], {type: 'text/pem'}));
	keyLink.download = 'RATTIC_PRIVATE_KEY.pem';
	
	document.body.appendChild(keyLink);
	keyLink.click();
	document.body.removeChild(keyLink);
    }
)
