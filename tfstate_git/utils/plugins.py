from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Generic, Type, TypeVar
from venv import logger


T = TypeVar("T")


@dataclass
class ProviderInstance(Generic[T]):
    name: str
    instance: T


@dataclass
class Provider(Generic[T]):
    name: str
    model_class: Type[T]


def get_providers_instances(provider_type: Type[T], entrypoint_group: str) -> dict[str, ProviderInstance[T]]:
    raw_providers = entry_points(group=entrypoint_group)

    providers_instances = {provider.name: provider.load() for provider in raw_providers}
    all_providers: dict[str, ProviderInstance[T]] = {}

    for provider_name, provider_instance in providers_instances.items():
        # check that provider_class is subclass of provider
        if not isinstance(provider_instance, provider_type):
            logger.warning(f"Provider {provider_name} is not an instance of {provider_type}")
            continue

        all_providers[provider_name] = ProviderInstance(provider_name, provider_instance)

    return all_providers


def get_providers(provider_type: Type[T], entrypoint_group: str) -> dict[str, Provider[T]]:
    raw_providers = entry_points(group=entrypoint_group)

    providers_classes = {provider.name: provider.load() for provider in raw_providers}
    all_providers: dict[str, Provider[T]] = {}

    for provider_name, provider_class in providers_classes.items():
        # check that provider_class is subclass of provider
        if not issubclass(provider_class, provider_type):
            logger.warning(f"Provider {provider_name} is not a subclass of {provider_type}")
            continue

        all_providers[provider_name] = Provider(provider_name, provider_class)

    return all_providers
