from hashlib import sha3_256
from base64 import b64decode, b64encode

from nacl.utils import random
from nacl.secret import SecretBox
from nacl.pwhash.argon2i import kdf


class CryptoAgent():

    def __init__(self, password, config):
        # we need to store salt

        salt = config.get('settings', 'salt')

        if salt:
            salt = b64decode(salt)

        else:
            salt = random(16)

        key = kdf(SecretBox.KEY_SIZE, bytes(password, 'utf-8'), salt)
        self.sbox = SecretBox(key)

        key = random(SecretBox.KEY_SIZE)
        password = random(len(password))

        config.set('settings', 'salt',
                   b64encode(salt).decode('utf-8'))

    def hash_value(self, value):

        sha3 = sha3_256()
        sha3.update(bytes(value, 'utf-8'))

        return sha3.hexdigest()

    def encrypt_value(self, value):

        encrypted = self.sbox.encrypt(bytes(value, 'utf-8'))

        return b64encode(encrypted).decode('utf-8')

    def decrypt_value(self, value):

        decoded = b64decode(value)

        return self.sbox.decrypt(decoded).decode('utf-8')
