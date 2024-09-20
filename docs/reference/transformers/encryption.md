# Encryption

![](https://img.shields.io/badge/Transformer Provider Type-encryption-purple)  

Encryption transformer is meant to be used to encyrpt and decrypt the terraform state file.  
It's built in a modular way to allow adding encryption providers easily.  

!!! note
    See [entrypoint](../general/04-entrypoints.md#terraflexpluginstransformerencryption) for additional information about the entrypoint.


## Usage

::: terraflex.plugins.encryption_transformation.encryption_transformation_provider.EncryptionTransformerConfig
    options:
      show_root_heading: false
      show_bases: false

## Encryption Protocol Specification

::: terraflex.plugins.encryption_transformation.encryption_base.EncryptionProtocol
    options:
      members: true