# Plugin Entrypoints

Terraflex is built in a modular way - that should be easily extendable by others - without the need of modifying terraflex itself and releasing new versions.  
A contribution is always welcome, but if you don't feel like it / have a capability and still want to use Terraflex's features - it's possible by the way Terraflex is implemented.  
Terraflex uses Python [entry_points()](https://docs.python.org/3/library/importlib.metadata.html#entry-points) to fetch all additinal extensions dynamically.  
More information about entry-points is available at the python packaging official [docs](https://packaging.python.org/en/latest/specifications/entry-points/).  

!!! note
    If you want to use your new extension with Terraflex - make sure the extension/plugin is installed in the same virtual env as Terraflex.  
    For example if you use pipx - you might need to use 
    ```console
    $ pipx inject terraflex <plugin>
    ```


## `terraflex.plugins.storage_provider`
Entrypoint that allows to extend the supported storage providers by Terraflex.  
The `type` of the storage provider will be the name of the entrypoint registered.  
Every provider must implement one of the storage provider protocols.

- [Readable storage](./02-storage-providers.md#terraflex.server.storage_provider_base.StorageProviderProtocol) - marked by - {% include-markdown "../../../docs_includes/badges-storage-provider-readable.md" %}
- [Writable storage](./02-storage-providers.md#terraflex.server.storage_provider_base.WriteableStorageProviderProtocol)  - marked by - {% include-markdown "../../../docs_includes/badges-storage-provider-writeable.md" %}
- [Lockable storage](./02-storage-providers.md#terraflex.server.storage_provider_base.LockableStorageProviderProtocol)  - marked by - {% include-markdown "../../../docs_includes/badges-storage-provider-lockable.md" %}

## `terraflex.plugins.transformer`
Entrypoint that allows to extend the supported transformers by Terraflex.  
The `type` of the transformer will be the name of the entrypoint registered.  
Every provider must implement the [transformer protocol](./03-transformers.md#terraflex.server.transformation_base.TransformerProtocol).  


## `terraflex.plugins.transformer.encryption`
Entrypoint that allows to extend the supported encryption types by Terraflex.  
The `type` of the transformer will be the name of the entrypoint registered.  
Every provider must implement the [encryption protocol](../transformers/encryption.md#terraflex.plugins.encryption_transformation.encryption_base.EncryptionProtocol).  
