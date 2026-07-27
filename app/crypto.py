"""
Hybrid AES/RSA encryption for outbound disbursement payloads.

Pattern: generate a fresh random AES-256 key per request, encrypt the
actual payload with AES-CBC, and encrypt only that (small, fixed-size)
AES key with the recipient's RSA public key. This avoids RSA's payload
size limits and is far faster than RSA-encrypting the whole payload
directly, while still giving the recipient a way to recover the AES
key using only their private key.

Demo keys only -- generate your own via `generate_demo_keypair()` and
never commit real private keys to source control.
"""

import base64
import json
import os
from typing import Any, Dict, Tuple

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad


def generate_demo_keypair(bits: int = 2048) -> Tuple[bytes, bytes]:
    """Generate an RSA keypair for local testing. Returns (private_pem, public_pem)."""
    key = RSA.generate(bits)
    return key.export_key(), key.publickey().export_key()


def encrypt_payload(payload: Dict[str, Any], recipient_public_key_pem: bytes) -> Dict[str, str]:
    """
    Encrypt a JSON-serializable payload for a recipient, given their RSA
    public key. Returns a dict of base64 strings safe to send over the wire.
    """
    aes_key = os.urandom(32)  # fresh AES-256 key per request
    iv = os.urandom(16)

    plaintext = json.dumps(payload).encode("utf-8")
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

    recipient_key = RSA.import_key(recipient_public_key_pem)
    rsa_cipher = PKCS1_OAEP.new(recipient_key)
    encrypted_aes_key = rsa_cipher.encrypt(aes_key)

    return {
        "encrypted_key": base64.b64encode(encrypted_aes_key).decode(),
        "iv": base64.b64encode(iv).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }


def decrypt_payload(envelope: Dict[str, str], private_key_pem: bytes) -> Dict[str, Any]:
    """Reverse of encrypt_payload -- recover the original JSON payload."""
    private_key = RSA.import_key(private_key_pem)
    rsa_cipher = PKCS1_OAEP.new(private_key)

    aes_key = rsa_cipher.decrypt(base64.b64decode(envelope["encrypted_key"]))
    iv = base64.b64decode(envelope["iv"])
    ciphertext = base64.b64decode(envelope["ciphertext"])

    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

    return json.loads(plaintext.decode("utf-8"))
