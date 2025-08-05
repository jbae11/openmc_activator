from pathlib import Path
import numpy as np
import openmc
import openmc.deplete
import os, tempfile
from typing import Sequence
import openmc.checkvalue as cv
from openmc.utility_funcs import change_directory
from openmc.deplete.microxs import _get_nuclides_with_data, _find_cross_sections
from openmc.deplete import REACTION_MT, GROUP_STRUCTURES, Chain
from typing import TypedDict
from packaging.version import Version
from openmc.data import ELEMENT_SYMBOL


class ActivationDict(TypedDict):
    """Contains necessary data for material activation calculations.
    
    This TypedDict defines the required parameters for performing activation
    calculations on materials using the deplete_materials function.
    """
    materials: openmc.Material
    """Material to be depleted during activation calculations"""
    
    multigroup_flux: Sequence[float]
    """Energy-dependent multigroup flux values, length must match energy groups"""
    
    energy: Sequence[float] | str
    """Energy group boundaries in [eV] or name of predefined group structure"""
    
    source_rate: Sequence[float]
    """Source rates for each timestep in the depletion calculation"""
    
    timesteps: Sequence[float]
    """Time intervals for the depletion steps in timestep_units"""


class OpenmcActivator:

    def __init__(
        self,
        activation_data: Sequence[ActivationDict],
        timestep_units: str = 's',
        reduce_chain_level: int = 5,
        chain_file: cv.PathLike | None = None,
        nuclides: Sequence[str] | None = None,
        reactions: Sequence[str] | None = None, 
        **init_kwargs: dict
    ):
        
        self.activation_data = activation_data
        self.timestep_units = timestep_units
        self.reduce_chain_level = reduce_chain_level
        self.chain_file = chain_file
        self.nuclides = nuclides
        self.reactions = reactions
        if init_kwargs == {}:
            self.init_kwargs = {'output': False}   


    def activate(self,
                 metric_list: list=['mass'],
                ) -> list[dict]:

        for entry in self.activation_data:
            material = entry['materials']
            assert material.temperature is not None, 'Material temperature must be set before depletion'

        msg = (
            'Chain file must be specified either in the OpenMC config or '
            'as an argument to OpenmcActivator'
        )
        if self.chain_file is None:
            if 'chain_file' not in openmc.config:
                raise ValueError(msg)
            self.chain_file = openmc.config['chain_file']
        if self.chain_file is None:
            raise ValueError(msg)
        chain_file_path = Path(self.chain_file).resolve()
        chain = Chain.from_xml(chain_file_path)

        # If no nuclides were specified, default to all nuclides from the chain
        if not self.nuclides:
            nuclides = chain.nuclides
            nuclides = [nuc.name for nuc in nuclides]
        else:
            nuclides = self.nuclides

        # Get reaction MT values. If no reactions specified, default to the
        # reactions available in the chain file
        if self.reactions is None:
            reactions = chain.reactions
        else:
            reactions = self.reactions
        mts = [REACTION_MT[name] for name in reactions]

        with change_directory(tmpdir=True):

            all_metric_dict = []

            for entry in self.activation_data:
                material = entry['materials']

                depleted_materials = material.deplete(
                    multigroup_flux=entry['multigroup_flux'],
                    energy_group_structure=entry['energy'],
                    timesteps=entry['timesteps'],
                    source_rates=entry['source_rate'],
                    timestep_units=self.timestep_units,
                    chain_file=chain,
                    reactions=reactions,
                )

                metric_dict = read_output(
                    materials=depleted_materials,
                    nuclides=nuclides,
                    metric_list=metric_list,
                    timesteps=entry['timesteps'],
                    timestep_units=self.timestep_units
                )
                all_metric_dict.append(metric_dict)
        return all_metric_dict
                


def read_output(
    materials:openmc.Materials,
    nuclides,
    metric_list:list,
    timesteps:list,
    timestep_units:str
):

    # get metrics
    # time is cumulative time
    metric_dict = {
    metric: {
            f'meta_time_{timestep_units}': [float(x) for x in np.cumsum([0] + list(timesteps))]
        }
        for metric in metric_list
    }
    # add all the isos
    for metric in metric_list:
        metric_dict[metric]['meta_total'] = []
        for iso in nuclides:
            metric_dict[metric][iso] = []
    for mat in materials:
        for metric in metric_dict.keys():
            if metric == 'mass':
                td = {iso:mat.get_mass(iso) for iso in nuclides}
            elif metric == 'atom':
                td = mat.get_nuclide_atoms()
            elif metric == 'decay_heat':
                td = mat.get_decay_heat('W', by_nuclide=True)
            elif metric == 'activity':
                td = mat.get_activity('Bq', by_nuclide=True)
            else:
                raise ValueError('Invalid metric ' + metric)
            
            for iso in nuclides:
                if iso not in td:
                    metric_dict[metric][iso].append(0.0)
                else:
                    metric_dict[metric][iso].append(td[iso])
            metric_dict[metric]['meta_total'].append(float(sum(td.values())))

    # Clean up the dictionary by removing entries with all zeros
    for metric in metric_dict.keys():
        for iso in nuclides:                
            # Check if all values are zeros
            if all(abs(value) == 0.0 for value in metric_dict[metric][iso]):
                # Remove entries that are all zeros
                del metric_dict[metric][iso]

    return metric_dict


def write_markdown_file(
    experiment_names: list[str],
    material_name: str,
):
    """A small utility function to write the Jupyter Book markdown files for
    each material irradiated:
    """

    element_names = {value: key for key, value in ELEMENT_SYMBOL.items()}

    # Create docs directory if it doesn't exist
    Path('docs').mkdir(exist_ok=True)
    
    filename = f'docs/{material_name}.md'
        
    with open(filename, 'w') as f:
        # Write the material header
        if material_name in element_names.keys():
            
            f.write(f'# {material_name} - {element_names[material_name]}\n\n')
        else:
            f.write(f'# {material_name}\n\n')
        
        # Write a section for each experiment
        for exp in experiment_names:
            f.write(f'## {exp}\n\n')

            f.write(f'<iframe src="../{material_name}_{exp}.html" width="100%" height="600px" frameborder="0"></iframe>\n\n')

            f.write(f'![Alt text]({material_name}_{exp}.png)\n\n')


def read_experimental_data(exp_file):
    """
    Read experimental data from file and filter out rows where all values are 0.
    
    Returns:
        tuple: (minutes, values, uncertainties) without any zero rows
    """
    lines = open(exp_file).readlines()
    
    minutes = []
    vals = []
    unc = []
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 3:
            continue
            
        min_val = float(parts[0])
        data_val = float(parts[1])
        unc_val = float(parts[2])
        
        # Skip rows where all three values are effectively zero
        if min_val == 0.0 and data_val == 0.0 and unc_val == 0.0:
            continue
            
        minutes.append(min_val)
        vals.append(data_val)
        unc.append(unc_val)
    
    return (minutes, vals, unc)