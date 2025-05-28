from pathlib import Path
import numpy as np
import openmc
import openmc.deplete
import os, tempfile
from typing import Sequence
import openmc.checkvalue as cv
from openmc.utility_funcs import change_directory
from openmc.deplete.microxs import _get_nuclides_with_data, _find_cross_sections, _resolve_chain_file_path
from openmc.deplete import REACTION_MT, GROUP_STRUCTURES, Chain
from typing import TypedDict


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
                ):

        for entry in self.activation_data:
            material = entry['materials']
            assert material.temperature is not None, 'Material temperature must be set before depletion'

        chain_file_path = _resolve_chain_file_path(Path(self.chain_file)).resolve()
        chain = Chain.from_xml(chain_file_path)

        cross_sections = _find_cross_sections(model=None)
        nuclides_with_data = _get_nuclides_with_data(cross_sections)

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

        # Create 3D array for microscopic cross sections
        microxs_arr = np.zeros((len(nuclides), len(mts), 1))

        # Create a material with all nuclides
        mat_all_nucs = openmc.Material()
        for nuc in nuclides:
            if nuc in nuclides_with_data:
                mat_all_nucs.add_nuclide(nuc, 1.0)
        mat_all_nucs.set_density("atom/b-cm", 1.0)

        # Create simple model containing the above material
        surf1 = openmc.Sphere(boundary_type="vacuum")
        surf1_cell = openmc.Cell(fill=mat_all_nucs, region=-surf1)
        model = openmc.Model()
        model.geometry = openmc.Geometry([surf1_cell])
        model.settings = openmc.Settings(
            particles=1, batches=1, output={'summary': False})

        with change_directory(tmpdir=True):
            # Export model within temporary directory
            model.export_to_model_xml()

            with openmc.lib.run_in_memory(**self.init_kwargs):
                # For each material, energy and multigroup flux compute the flux-averaged cross section for the nuclides and reactions

                all_metric_dict = []
                for entry in self.activation_data:
                    material = entry['materials']
                    multigroup_flux = entry['multigroup_flux']
                    energy = entry['energy']
                    source_rates = entry['source_rate']
                    timesteps = entry['timesteps']

                    # Normalize multigroup flux
                    multigroup_flux = np.array(multigroup_flux)
                    multigroup_flux /= multigroup_flux.sum()

                    # check_type("temperature", temperature, (int, float))
                    # if energy is string then use group structure of that name
                    if isinstance(energy, str):
                        energy = GROUP_STRUCTURES[energy]
                    else:
                        # if user inputs energy check they are ascending (low to high) as
                        # some depletion codes use high energy to low energy.
                        if not np.all(np.diff(energy) > 0):
                            raise ValueError('Energy group boundaries must be in ascending order')

                    # check dimension consistency
                    if len(multigroup_flux) != len(energy) - 1:
                        msg = 'Length of flux array should be len(energy)-1, but ' \
                            f'got {len(multigroup_flux)} multigroup_flux entries ' \
                            f'and {len(energy)} energy group boundaries'
                        raise ValueError(msg)

                    for nuc_index, nuc in enumerate(nuclides):
                        if nuc not in nuclides_with_data:
                            continue
                        lib_nuc = openmc.lib.nuclides[nuc]
                        for mt_index, mt in enumerate(mts):
                            xs = lib_nuc.collapse_rate(
                                mt, material.temperature, energy, multigroup_flux
                            )
                            microxs_arr[nuc_index, mt_index, 0] = xs

                    micro_xs = openmc.deplete.MicroXS(microxs_arr, nuclides, reactions)

                    operator = openmc.deplete.IndependentOperator(
                        materials=openmc.Materials([material]),
                        fluxes=[material.volume],
                        micros=[micro_xs],
                        normalization_mode='source-rate',
                        reduce_chain_level=5,
                        chain_file=chain_file_path
                    )

                    integrator = openmc.deplete.PredictorIntegrator(
                        operator=operator,
                        timesteps=timesteps,
                        source_rates=source_rates,
                        timestep_units=self.timestep_units
                    )

                    integrator.integrate(path='temp_results.h5')

                    metric_dict = read_output(
                        output_path='temp_results.h5',
                        nuclides=nuclides,
                        metric_list=metric_list,
                        timesteps=timesteps,
                        material_id=material.id,
                        timestep_units=self.timestep_units
                    )
                    all_metric_dict.append(metric_dict)
        return all_metric_dict
                


def read_output(
    output_path:str,
    nuclides,
    metric_list:list,
    timesteps:list,
    material_id:str,
    timestep_units:str
):

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

    return metric_dict

