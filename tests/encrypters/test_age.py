import pytest


@pytest.mark.anyio
async def test_encrypt_decrypt(age_controller):
    to_encyrpt = b"hello world"
    encrypted = await age_controller.encrypt("test", to_encyrpt)
    decrypted = await age_controller.decrypt("test", encrypted)

    assert decrypted == to_encyrpt
