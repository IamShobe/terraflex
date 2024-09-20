# Age

![](https://img.shields.io/badge/Encryption Provider Type-age-purple)  

Uses [age](https://github.com/FiloSottile/age) file encryption.  

!!! Note
    You don't need to have `age` binary installed in your `PATH` - terraflex plugin will automatically download a compatible plugin.

Age encryption type works with the [Encryption](../transformers/encryption.md) state transformer.  
The encryption plugin was designed to work with any {% include-markdown "../../../docs_includes/badges-storage-provider-readable.md" %} type storage provider (basically any storage provider).  
The recommended storage providers are: [EnvVar](../storage-providers/envvar.md) or [1Password](../storage-providers/onepassword.md) if owned, but you can always use [Local](../storage-providers/local.md) storage provider or even a custom built storage provider.


!!! Warning
    Do not lose your private key - if you already started using Terraflex with the encryption key - and you lost your encryption key -  
    **there is no way to recover the state file**.

!!! Tip
    Use [1Password](../storage-providers/onepassword.md) storage provider if possible to make it much more less probable for you to lose your encryption key.

## Usage

::: terraflex.plugins.encryption_transformation.age.provider.AgeKeyConfig
    options:
      show_root_heading: false
      show_bases: false

## Example

Here is an example for a config file that uses age encryption:  

```yaml hl_lines="12-16" title="terraflex.yaml"
{%
  include "../../../examples/age-encryption-envvar.yaml"
%}
```
