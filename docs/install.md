# Install

First clone or otherwise [download](https://github.com/jbae11/openmc_activator/archive/refs/heads/main.zip) the repository and cd into the director

```bash
git clone git@github.com:jbae11/openmc_activator.git
cd openmc_activator
```

Next install the Python packages that are needed to run the notebook. These can be installed from the [requirements file](https://github.com/jbae11/openmc_activator/blob/main/requirements.txt).

This includes a development version of OpenMC from the current develop branch (13/June/2025)

Pick the version of Python you have installed
```
pip install -r requirements_3.10.txt
pip install -r requirements_3.11.txt
pip install -r requirements_3.12.txt
```

You could alternatively [install OpenMC from source (develop branch needed)](https://docs.openmc.org/en/stable/usersguide/install.html#installing-from-source) and install the remaining requirements with
```
pip install -r requirements.txt
```