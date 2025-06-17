[![Jupyter Book Badge](https://jupyterbook.org/badge.svg)](https://jbae11.github.io/openmc_activator/)

[![CI testing](https://github.com/jbae11/openmc_activator/actions/workflows/ci.yml/badge.svg)](https://github.com/jbae11/openmc_activator/actions/workflows/ci.yml)

# openmc_activator

Standalone openmc activator to get activated composition from MG flux and irradiation scheme.

## See the [online documentation for installation, getting started and simulation results](https://jbae11.github.io/openmc_activator/) :link:

The module is tested on the [Fusion Neutron Source (FNS) Decay Heat Benchmark](https://nds.iaea.org/conderc/fusion/)

This module is actually part of the Fusion Energy Reactor Models Integrator (FERMI) [project](https://code.ornl.gov/4ib/fermi). A similar module exists for ORIGEN.

# Contents
1. `compare.ipynb`: Jupyter notebook going through the process of using `OpenmcActivator` to reproduce FNS benchmark with OpenMC and comparing the results
2. `openmc_activator.py`: Python class for standalone neutron source activation with OpenMC
