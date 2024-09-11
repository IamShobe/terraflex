from typing import get_args

from tfstate_git.server.config import (
    STORAGE_PROVIDER_TYPE_TO_PARAMS,
    OneOfStorageProviderConfig,
)


def test_config_keys_all_defined():
    annotated_types = get_args(OneOfStorageProviderConfig)
    union_types = get_args(annotated_types[0])  # first element is the Union type

    registered_config_types = [
        get_args(c.__annotations__["type"])[0] for c in union_types
    ]
    all_types = list(STORAGE_PROVIDER_TYPE_TO_PARAMS.keys())

    # assert all storage providers have a corresponding class in STORAGE_PROVIDER_TYPE_TO_PARAMS
    assert all(config_type in all_types for config_type in registered_config_types)
