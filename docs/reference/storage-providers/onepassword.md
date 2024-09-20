# 1Password

![](https://img.shields.io/badge/Storage Provider Type-onepassword-purple)  

{% include-markdown "../../../docs_includes/badges-storage-provider-readable.md" %}

1Password storage providers allows to read vault items and pass them around to a consumer - like a transformer.  
If you have a 1Password account it's highly recommended to keep your encryption private key stored there.  

{% include-markdown "../../../docs_includes/readonly-storage-providers.md" %}

## Initialization

::: terraflex.plugins.onepassword_storage_provider.onepassword_storage_provider.OnePasswordStorageProviderInitConfig
    options:
      show_bases: false

## ItemKey

::: terraflex.plugins.onepassword_storage_provider.onepassword_storage_provider.OnePasswordProviderItemIdentifier

## Example

```yaml title="terraflex.yaml" hl_lines="6-7 14-16"
{%
  include "../../../examples/age-encryption-1password.yaml"
%}
```