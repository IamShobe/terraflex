# Intro

Terraflex is built in a modular way.  
To start configuring Terraflex yourself and even build your own plugins you will need to know few building blocks that Terraflex uses.  
Terraflex uses Terraform's [http backend](https://developer.hashicorp.com/terraform/language/backend/http) behind the scenes to serve and manage the Terraform state files.


## Concepts

Terraflex's building blocks are:

- [Terraform Stack](#terraform-stack)
- [Storage provider](#storage-provider)
- [Transformer](#transformer)

### Terraform Stack
In Terraflex you can manage multiple Terraform state files - that are independent from each other.  
This allows you to have a single [`terraflex.yaml`](../reference/general/01-terraflex_yaml.md) file (the config file of Terraflex) in your mono repo 
and use multiples backends - one for each Terraform state file.  
Each state file - is refered as a Terraform stack.  
And each stack consists of a main [storage provider](#storage-provider) to manage the state at, and a list of transformers that allows you to manipulate the state file -  
used for stuff like [encryption](../reference/transformers/encryption.md).

A stack is defined in `terraflex.yaml` under the `stacks` directive.

!!! example
    ```yaml title="terraflex.yaml"
    stacks:
      stack-123: # this can be any name you would like - note that it will affect the http backend url.
        transformers:
          - transformer1
          - transformer2
        state_storage:
          provider: storage-provider-1
          params:
            path: terraform.tfstate
    ```

This structure allows you to define different stacks and each stack to have it's own transformer or storage class if required.  

See reference [here](../reference/general/01-terraflex_yaml.md#terraflex.server.config.StackConfig).

### Storage provider

Storage providers are an abstract way to allow file saving and reading.  
It can be used either to store the Terraform state file - or even to use for extensions in [transformers](#transformer).  
For example [age](../reference/encryption-providers/age.md) encryption provider uses a generic storage provider approach to fetch it's private key from a configurable source.  

A storage provider is defined under the `storage_providers` directive inside `terraflex.yaml`.

!!! example
    ```yaml title="terraflex.yaml"
    storage_providers:
      git-storage: # Initialize new storage provider - name can be anything
        type: git # In this case we use `git` storage provider
        origin_url: git@github.com:IamShobe/tf-state.git
    ```

See reference [here](../reference/general/02-storage-providers.md).

### Transformer

Transformer is a middleware between the state storing and reading that allows you to manipulate the state file in different ways.  
An example for such transformer is the [encryption](../reference/transformers/encryption.md) transformer - that allows you to encrypt the state file before it's stored in the storage provider, and decrypt the state file after it's read from it.

A transformer is defined under the `transformers` directive inside `terraflex.yaml`.

!!! example
    ```yaml title="terraflex.yaml"
    transformers:
      encryption: # Initialize new transformer - Name can be anything, we use `encryption` for semantics.
        type: encryption # In this case we use `encryption` transformer
        key_type: age # We use `age` as the encryption provider
        import_from_storage:
          provider: envvar-example # Make sure name is matching your storage provider
          params:
            key: AGE_KEY # The environment variable name to use for the encryption key
    ```

See reference [here](../reference/general/03-transformers.md).

## What's next?

Check out the [getting started](./guides/01-setting-up-git.md) guides to jump right on the action.  
Also go to the [reference](../reference/general/01-terraflex_yaml.md) to learn a little bit more about `terraflex.yaml` and the diffrent component it has.  
