import pytest

from tfstate_git.plugins.encryption_transformation.encryption_transformation_provider import EncryptionTransformation


@pytest.mark.anyio
async def test_app(age_controller):
    transformation = EncryptionTransformation(
        encryption_provider=age_controller,
    )

    to_encrypt = b"hello world"
    result = await transformation.transform_write_file_content("test", to_encrypt)
    decrypted = await transformation.transform_read_file_content("test", result)
    assert decrypted == to_encrypt
