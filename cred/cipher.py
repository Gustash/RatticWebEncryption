import base64
import hashlib
import Crypto
import ast
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA

import logging

logger = logging.getLogger(__name__)

class AESCipher(object):

    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

    # This method meshes two strings together
    @staticmethod
    def mesh(s1, s2):
        return "".join(i + j for i, j in zip(s1, s2))

class key_rsa:
    key = None

    def __init__(self, key=None):
	if key:
	    self.key = key
	else:
	    self.key = RSA.generate(2048, Random.new().read)

    def encrypt(self, password):
	return self.key.publickey().encrypt(password, 32)

    def decrypt(self, password):
	return self.key.decrypt(ast.literal_eval(str(password)))

    def save_key(self, file):
	logger.info("Saving into: " + file)
	f = open(file, 'w')
	f.write(self.key.exportKey('PEM'))
	f.close()

    @staticmethod
    def load_key(file):
	f = open(file, 'r')
	key = key_rsa(RSA.importKey(f.read()))
	f.close()
	return key
