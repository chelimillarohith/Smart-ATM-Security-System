try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Random import get_random_bytes
except ImportError:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes

KEY = b'Sixteen byte keySixteen byte key'

def encrypt(data: bytes) -> bytes:
    iv = get_random_bytes(12)
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return iv + tag + ciphertext

def decrypt(data: bytes) -> bytes:
    iv = data[:12]
    tag = data[12:28]
    ciphertext = data[28:]
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=iv)
    return cipher.decrypt_and_verify(ciphertext, tag)
