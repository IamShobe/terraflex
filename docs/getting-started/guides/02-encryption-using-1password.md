# Encryption using 1Password

Checkout [1Password Reference](../../reference/storage-providers/onepassword.md).  
Also checkout [1Password Full Example](../examples/1password-storage-provider.md).  
Checkout IAC [repo example](https://github.com/IamShobe/iac-terraflex-example/tree/1password).  

## Creating new item in 1Password

Copy the content of the created key from [previous guide](./01-setting-up-git.md):
```console
$ cat ~/secrets/age-key.txt # make sure the file name matches your created key!

$ cat ~/secrets/age-key.txt | pbcopy  # in Mac you can use pycopy to copy it to your clipboard right away

$ cat ~/secrets/age-key.txt | xclip -selection clipboard  # with xclip
```

Create new login item in 1Password - 
In my case I will create a new Vault named `AutomationIAC`, and a new login item named `iac-terraform-age-key`.

Inside the `password` field paste the content of your copied private key.

Then we will construct the [`reference uri`](https://developer.1password.com/docs/cli/secret-reference-syntax/) for that private key.  
The structure of the `refrence uri` is: `op://<vault>/<item>/<field>`.  
This means that my private key reference uri is compose into:  
`op://AutomationIAC/iac-terraform-age-key/password`.


## Modifying `terraflex.yaml`
Using 1Password as the encryption storage provider is as simple as editing the `terraflex.yaml` file generated from the [previous guide](./01-setting-up-git.md).  

Change the storage provider used by the `encryption` to be of type `onepassword`:
```yaml
storage_providers:
  encryption:
    type: onepassword
```

In the encyrption transformer make sure to update the parameters for your 1Password item:
```yaml
transformers:
  encryption: # Initialize new transformer - Name can be anything, we use `encryption` for semantics.
    type: encryption # In this case we use `encryption` transformer
    key_type: age # We use `age` as the encryption provider
    import_from_storage:
      provider: encryption # Make sure name is matching your storage provider
      params:
        reference_uri: op://AutomationIAC/iac-terraform-age-key/password # The reference URI to use for the encryption key
```
Change the `reference uri` according to your created item.

That's it we are done!  
Try to run any Terraform command that uses the state - to make sure everything works.  
```console
$ terraflex wrap -- terraform plan
```


## Cleanups
You can now remove the old secret from the disk so the only source of truth will be 1Password.
```console
$ rm ~/secrets/age-key.txt
```