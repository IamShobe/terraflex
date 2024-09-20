# EnvVar

![](https://img.shields.io/badge/Storage Provider Type-envvar-purple)  

{% include-markdown "../../../docs_includes/badges-storage-provider-readable.md" %}

EnvVar storage providers allows to read environment variables and pass them around to consumer - like a transformer.  

{% include-markdown "../../../docs_includes/readonly-storage-providers.md" %}

## Initialization

::: terraflex.plugins.envvar_storage_provider.envvar_storage_provider.EnvVarStorageProviderInitConfig
    options:
      show_bases: false

## ItemKey

::: terraflex.plugins.envvar_storage_provider.envvar_storage_provider.EnvVarStorageProviderItemIdentifier

## Example

```yaml title="terraflex.yaml" hl_lines="6-7 14-16"
{%
  include "../../../examples/age-encryption-envvar.yaml"
%}
```