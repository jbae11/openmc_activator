import numpy as np
import openmc.deplete
import openmc
import os, tempfile
from typing import Sequence
import openmc.checkvalue as cv
from openmc.deplete.microxs import _get_nuclides_with_data, _find_cross_sections, _resolve_chain_file_path
from openmc.deplete import REACTION_MT, GROUP_STRUCTURES, Chain


class ActivationDict(TypedDict):
    materials: openmc.Materials
    multigroup_fluxes: Sequence[float]
    scores: list[float]
    energy: Sequence[float] | str
    source_rate: Sequence[float]

class OpenmcActivator:

    def __init__(
        self,
        activation_data: Sequence[ActivationDict],
        timestep_units: str = 's',
        reduce_chain_level: int = 5,
        chain_file: cv.PathLike | None = None,
        nuclides: Sequence[str] | None = None,
        reactions: Sequence[str] | None = None,       
    ):
        
        self.activate_data = activation_data
        self.timestep_units = timestep_units
        self.reduce_chain_level = reduce_chain_level
        self.chain_file = chain_file
        self.nuclides = nuclides
        self.reactions = reactions
        

    def activate(self,
                 metric_list: list=['mass'],
                ):

        cross_sections = _find_cross_sections(model=None)
        nuclides_with_data = _get_nuclides_with_data(cross_sections)

        # If no nuclides were specified, default to all nuclides from the chain
        if not nuclides:
            chain = Chain.from_xml(_resolve_chain_file_path(self.chain_file))
            nuclides = chain.nuclides
            nuclides = [nuc.name for nuc in nuclides]


        return read_output(self.nuclides, metric_list, timesteps, material.id,
                           self.timestep_units)


def read_output(output_path:str, nuclides, metric_list:list, timesteps:list, material_id:str,
                timestep_units:str):

    results = openmc.deplete.ResultsList.from_hdf5(output_path)

    # get metrics
    # time is cumulative time
    metric_dict = {metric: {'meta_time_%s' %timestep_units: np.cumsum([0] + list(timesteps))} for metric in metric_list}
    # add all the isos
    tmp_mat = results[0].get_material(str(material_id))
    for metric in metric_list:
        metric_dict[metric]['meta_total'] = []
        for iso in nuclides:
            metric_dict[metric][iso] = []
    for result in results:
        mat = result.get_material(str(material_id))

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
            metric_dict[metric]['meta_total'].append(sum(td.values()))

    if remove:
        os.remove(output_path)

    return metric_dict

