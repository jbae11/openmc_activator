# Install

First clone or otherwise [download](https://github.com/jbae11/openmc_activator/archive/refs/heads/main.zip) the repository and cd into the director

```bash
git clone git@github.com:jbae11/openmc_activator.git
cd openmc_activator
```

Optionally create a new virtual environment

```bash
sudo apt-get --yes install python3-venv
python3 -m venv .new_env
source .new_env/bin/activate
```

Next install the Python packages that are needed to run the notebook. These can be installed from the [requirements file](https://github.com/jbae11/openmc_activator/blob/main/requirements.txt).

This includes a development version of OpenMC from [this branch](https://github.com/shimwell/openmc/tree/making-wheel-3) which allows Python wheels to be built.

```
pip install -r requirements.txt
```

You could alternatively [install OpenMC from source (develop branch needed)](https://docs.openmc.org/en/stable/usersguide/install.html#installing-from-source) and install the remaining requirements with
```
pip install -r requirements.txt
```