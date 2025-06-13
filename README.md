[![CI testing](https://github.com/jbae11/openmc_activator/actions/workflows/ci.yml/badge.svg)](https://github.com/jbae11/openmc_activator/actions/workflows/ci.yml)

# openmc_activator

Standalone openmc activator to get activated composition from MG flux and irradiation scheme.

The module is tested on the [Fusion Neutron Source (FNS) Decay Heat Benchmark](https://nds.iaea.org/conderc/fusion/)

This module is actually part of the Fusion Energy Reactor Models Integrator (FERMI) [project](https://code.ornl.gov/4ib/fermi). A similar module exists for ORIGEN.

# Installation

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

# Run the V&V

Run the `compare.ipynb` to perform the OpenMC simulations and compare them with precalculated FISPACT results and CoNDERC experimental data.

This can be run in several ways.

- With Jupyter Lab
    ```
    jupyter lab compare.ipynb
    ```

- With Jupyter
    ```
    jupyter notebook compare.ipynb
    ```

- With VS Code, assuming you have the Jupyter extension installed
    ```
    code compare.ipynb 
    ```

- Convert it to a python file and run with Python
    ```
    jupyter nbconvert compare.ipynb --to python
    python compare.py
    ```

- Build the book with Jupyter books.
    ```
    jupyter-book build .
    ```

# Contents
1. `compare.ipynb`: Jupyter notebook going through the process of using `OpenmcActivator` to reproduce FNS benchmark with OpenMC and comparing the results
2. `openmc_activator.py`: Python class for standalone neutron source activation with OpenMC
