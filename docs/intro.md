# OpenMC depletion V&V.

This book presents a comprehensive comparison of OpenMC depletion calculations against established open benchmarks.

Open benchmarks provide superior reproducibility and seamless integration capabilities compared to proprietary alternatives, making them the primary focus of this comparative study. There are publications in the area of OpenMC depletion V&V which might also be of interest [[1]](https://www.sciencedirect.com/science/article/pii/S0920379624005647) and [[2]](https://iopscience.iop.org/article/10.1088/1741-4326/ad32dd/meta).

The analysis centers on the [CoNDERC Dataset from the IAEA’s FNS Fusion Decay-Heat Benchmark](https://www-nds.iaea.org/conderc/fusion/), which represents one of the most comprehensive validation datasets available in the field. This extensive benchmark suite encompasses experimental data from the irradiation of 69 individual elements and 4 composite materials across three distinct irradiation campaigns conducted at the FNS facility. In total this provides 132 irradiation experiments each with several data points in time. 

The following chapters detail both the experimental results and systematic code-to-code comparisons, providing readers with thorough validation data for OpenMC’s depletion capabilities and insights into its performance relative to other computational approaches.

The results presented are entirely reproducible by following the steps outlined in the [GitHub repository README.md](https://github.com/jbae11/openmc_activator). Note the use of a [specific OpenMC depletion chain file tuned for the fusion neutron spectra](https://github.com/jbae11/openmc_activator/blob/main/fns_spectrum.chain.xml). Further more the results are sufficiently easy to reproduce with each change to OpenMC (release or a single commit) and therefore the repository could act as document of how the results change with OpenMC evolution.



```{tableofcontents}
```
