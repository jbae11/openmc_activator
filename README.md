[![CI testing](https://github.com/jbae11/openmc_activator/actions/workflows/ci.yml/badge.svg)](https://github.com/jbae11/openmc_activator/actions/workflows/ci.yml)

# openmc_activator

Standalone openmc activator to get activated composition from MG flux and irradiation scheme.

The module is tested on the [Fusion Neutron Source (FNS) Decay Heat Benchmark](https://nds.iaea.org/conderc/fusion/)

This module is actually part of the Fusion Energy Reactor Models Integrator (FERMI) [project](https://code.ornl.gov/4ib/fermi). A similar module exists for ORIGEN.

# Contents
1. `download_fns_fusion_decay.py`: Script to download and extract the FNS benchmark data files from website
2. `compre.ipynb`: Jupyter notebook going through the process of using `OpenmcActivator` to reproduce FNS benchmark with OpenMC and comparing the results
3. `openmc_activator.py`: Python class for standalone neutron source activation with OpenMC
