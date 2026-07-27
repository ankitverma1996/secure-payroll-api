from app.crypto import generate_demo_keypair, encrypt_payload, decrypt_payload


def test_roundtrip_encrypt_decrypt():
    private_pem, public_pem = generate_demo_keypair()
    payload = {"worker_id": "W1", "amount": "1234.56"}

    envelope = encrypt_payload(payload, public_pem)
    assert set(envelope.keys()) == {"encrypted_key", "iv", "ciphertext"}

    recovered = decrypt_payload(envelope, private_pem)
    assert recovered == payload


def test_fresh_aes_key_per_call():
    # Two calls with the same payload should NOT produce the same
    # ciphertext, since a fresh AES key + IV is generated per request.
    private_pem, public_pem = generate_demo_keypair()
    payload = {"worker_id": "W1", "amount": "1234.56"}

    envelope_1 = encrypt_payload(payload, public_pem)
    envelope_2 = encrypt_payload(payload, public_pem)

    assert envelope_1["ciphertext"] != envelope_2["ciphertext"]
    assert envelope_1["encrypted_key"] != envelope_2["encrypted_key"]
