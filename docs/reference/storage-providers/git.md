# Git

![](https://img.shields.io/badge/Storage Provider Type-git-purple)  

{% include-markdown "../../../docs_includes/badges-all.md" %}

Git storage provider is capable of holding terraform state files as it's a writable storage type.  
This provider is also lockable - and because this storage type is backed up by a remote origin usually - 
it allows multiple users to work on the same state files without the risk of overriding eachother (the lock should protect the state file).  
This storage provider was heavily influenced by [terraform-backend-git](https://github.com/plumber-cd/terraform-backend-git).  

!!! danger

    It's highly recommended to **not use this provider plainly without any transformer** for the state file - as state files contains [sensitive data](https://developer.hashicorp.com/terraform/language/state/sensitive-data).  
    See [encryption](../transformers/encryption.md) transformer, to make git storage provider a viable solution to store terraform state files - 
    without any additional cost - and with a minimal setup required.

## Initialization

::: terraflex.plugins.git_storage_provider.git_storage_provider.GitStorageProviderInitConfig
    options:
      show_bases: false

## ItemKey

::: terraflex.plugins.git_storage_provider.git_storage_provider.GitStorageProviderItemIdentifier

## Example

```yaml title="terraflex.yaml" hl_lines="2-4 23-25"
{%
  include "../../../examples/age-encryption-envvar.yaml"
%}
```
