# Installation

Installing Terraflex should be as simple as using [pipx](https://github.com/pypa/pipx) install.  
If you don't already have `pipx` installed on your computer, please refer to their docs to install it first.  
`pipx` allows Terraflex to be installed in an isolated environments - which reduces anomalies - and global workspace pollution.  

```console
$ pipx install terraflex
```

To upgrade terraflex use:
```console
$ pipx upgrade terraflex
```

You can also upgrade the python version that Terraflex is using:
```console
$ pipx reinstall terraflex --python=<path to newer python binary>
```

If you don't want to use `pipx` you can still use `pip` to install Terraflex in your global environment.
