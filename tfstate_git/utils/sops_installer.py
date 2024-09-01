import pathlib
import platform

import httpx

VERSION = "3.9.0"

PLATFORM_TO_BIN_NAME = {
    "linux_arm64": "sops-v{version}.linux.arm64",
    "linux_amd64": "sops-v{version}.linux.amd64",
    "darwin_amd64": "sops-v{version}.darwin.amd64",
    "darwin_arm64": "sops-v{version}.darwin.arm64",
}


def get_platform_key():
    return f"{platform.system().lower()}_{platform.machine().lower()}"


def get_bin_name(version):
    bin_name = PLATFORM_TO_BIN_NAME.get(get_platform_key())
    if bin_name is None:
        raise Exception(f"Unsupported platform: {get_platform_key()}")

    return bin_name.format(version=version)


async def download_sops(dest_folder: pathlib.Path, version=VERSION):
    bin_name = get_bin_name(version)
    print('Downloading sops client...')
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://github.com/getsops/sops/releases/download/v{version}/{bin_name}",
            follow_redirects=True,
        )

        if response.status_code != 200:
            raise Exception(f"Failed to download sops: {response.status_code} - {response.text}")

    # create directory if it doesn't exist
    dest_folder.mkdir(parents=True, exist_ok=True)
    # ideally we would want it to be async, but for now we can just do it sync..
    output_bin = dest_folder / bin_name
    with open(output_bin, "wb") as f:
        f.write(response.content)

    # make it executable
    output_bin.chmod(0o755)

    return bin_name


async def bootstrap(dest_folder: pathlib.Path, version=VERSION):
    bin_name = get_bin_name(version)
    expected_bin_location = dest_folder / bin_name
    if expected_bin_location.exists():
        print('Sops client already exists!')
        return expected_bin_location

    return await download_sops(dest_folder, version)
