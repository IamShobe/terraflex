# Local

![](https://img.shields.io/badge/Storage Provider Type-local-purple)  
{% include-markdown "../../../docs_includes/badges-all.md" %}

The most basic storage provider - that uses local disk paths.  
It can be used for basic rigging over local disk paths.  

!!! tip
    This provider allow you to use shared disk paths as well - like NFS folders or FUSE mounts using [rclone](https://rclone.org/commands/rclone_mount/)


## Initialization

::: terraflex.plugins.local_storage_provider.local_storage_provider.LocalStorageProviderInitConfig
    options:
      show_bases: false

## ItemKey

::: terraflex.plugins.local_storage_provider.local_storage_provider.LocalStorageProviderItemIdentifier

## Example

```yaml title="terraflex.yaml" hl_lines="2-4 6-8 15-17 24-26"
{%
  include "../../../examples/age-encryption-local-all.yaml"
%}
```
