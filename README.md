# openmc_activator
Standalone openmc activator to get activated composition from MG flux and irradiation scheme.

The module is tested on the [Fusion Neutron Source (FNS) Decay Heat Benchmark](https://nds.iaea.org/conderc/fusion/)

This module is actually part of the Fusion Energy Reactor Models Integrator (FERMI) [project](https://code.ornl.gov/4ib/fermi). A similar module exists for ORIGEN.

# Contents
1. `download_fns_fusion_decay.py`: Script to download and extract the FNS benchmark data files from website
2. `compre.ipynb`: Jupyter notebook going through the process of using `OpenmcActivator` to reproduce FNS benchmark with OpenMC and comparing the results
3. `openmc_activator.py`: Python class for standalone neutron source activation with OpenMC


## Note
The jupyter notebook in this repository will not yield results similar to the FNS decay heat benchmark, due to not incorportaing nuclide reaction yield data (e.g., Ag107 -> (n,gamma) -> Ag108 or Ag108m). This was resovled by the original author by using ORIGEN multigroup nuclide reaction yield data to append flux-normalized `branch_ratios` in the chain file. That data, unfortunately, cannot be shared in this public repository. [This issue in the OpenMC git repo](https://github.com/openmc-dev/openmc/issues/2757) details this issue in OpenMC, and disucssions on potential longer-term solutions.
