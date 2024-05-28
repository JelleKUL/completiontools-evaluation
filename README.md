# completiontools-evaluation
The evaluation code for the completion tools

## Getting Started
This document is meant to keep track of all your work, use it to track sources, progress and problems.

### Open3d
Most of the code will be using the open-source package [open3d](www.open3d.com). Take a look at the documentation for more info: [open3d.com/docs](www.open3d.com/docs)

#### install open3d on MacOS & Windows
```
pip install open3d
```

### Installing the environment

1. Download `python 3.9` from: [python.org](www.python.org)
2. Enter the following commands in the `terminal`
    ``` bash
    # Windows
    # Create the virtual environment
    py -3.9 -m venv env
    # Activate the virtual environment
    ./env/Scripts/activate
    # Install the packages
    pip install -r requirements.txt
    ```
    
    ``` bash
    # MacOS / Linux
    # Create the virtual environment
     python3 -m venv "env name"
    # Activate the virtual environment
    source "env name"/bin/activate
    # Install the packages
    pip install -r requirements.txt
    ``` 

### Removing pip packages plus all its dependencies
``` bash
# install pip-autoremove
pip install pip-autoremove
# remove "package" plus its dependencies:
pip-autoremove "package" -y
```

## Thesis
https://www.overleaf.com/3584264975pqwgqhngknpp#422092
