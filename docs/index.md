# Terraflex

[![](https://img.shields.io/pypi/v/terraflex)](https://pypi.org/project/terraflex/) ![](https://img.shields.io/pypi/pyversions/terraflex)

## Useful links

- [Getting started](./getting-started/01-intro.md)
- Checkout [issues](https://github.com/IamShobe/terraflex/issues) to see roadmap.

## Intro
Construct custom backends for your terraform project!

!!! WARNING
    This project is still WIP in early stages - there might be some bugs - you are welcome to open issues when any encounted

#### why?
I started this project to provide a free solution for **homelabs** IAC.  
The major constraint here is to find a **free** backend that I feel **safe** to use and to have a 0 bootstrap layer if possible.  
I found several solutions around this - but most were using a 3rd party hosted [http](https://developer.hashicorp.com/terraform/language/backend/http) backend servers.  
Those backends were problematic for me because I had issues trusting them to store my sensitive state files - and the fact that I didn't own the storage location - made me afraid that I might lose those state files - and we all know how bad it is to lose your state files :P.  
The closest solution I found was [terraform-backend-git](https://github.com/plumber-cd/terraform-backend-git) - which this project was heavily influenced on - so go check it out as well!  
Eventually I had the idea of creating an **extendable modular terraform http backend** - which allows customizing the state using `transformations` (like encryption), and getting starting with it will be as simple as running single command.
