import pytest

from tfstate_git.plugins.encryption_transformation.age.controller import AgeController, AgeKeygenController
from tfstate_git.plugins.encryption_transformation.age.downloader import AgeDownloader
from tfstate_git.utils.dependency_downloader import DependencyDownloader

pytestmark = pytest.mark.anyio


@pytest.fixture(scope='module')
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def age_gen_controller(tmp_path):
    downloader = DependencyDownloader(
        names=["age", "age-keygen"],
        version="1.2.0",
        downloader=AgeDownloader(),
    )

    await downloader.ensure_installed(tmp_path)
    return AgeKeygenController(
        binary_location=tmp_path / "age-keygen-v1.2.0",
    )


@pytest.fixture
async def age_controller(tmp_path, age_gen_controller):
    private_key = await age_gen_controller.generate_key_bytes()
    pub_key = await age_gen_controller.get_public_key_from_bytes(private_key)

    return AgeController(
        binary_location=tmp_path / "age-v1.2.0",
        private_key=private_key,
        public_key=pub_key,
    )
