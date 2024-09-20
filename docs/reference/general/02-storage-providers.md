# Storage Provider Types

Storage provider is one of the building blocks in `Terraflex` -  
it defines an abstract way to communicate with a storage of any kind.  
A new storage provider can easily be provided by implementing one of the protocols below - 
and registering into [`terraflex.plugins.storage_provider`](./04-entrypoints.md#terraflexpluginsstorage_provider) entrypoint.

## Readable Storage
{% include-markdown "../../../docs_includes/badges-storage-provider-readable.md" %}

::: terraflex.server.storage_provider_base.StorageProviderProtocol
    options:
      show_bases: false
      members: true

::: terraflex.server.storage_provider_base.ItemKey
    options:
      members: true

## Writeable Storage
{% include-markdown "../../../docs_includes/badges-storage-provider-writeable.md" %}

::: terraflex.server.storage_provider_base.WriteableStorageProviderProtocol
    options:
      members: true

## Lockable Storage
{% include-markdown "../../../docs_includes/badges-storage-provider-lockable.md" %}

::: terraflex.server.storage_provider_base.LockableStorageProviderProtocol
    options:
      members: true

::: terraflex.server.storage_provider_base.LockBody