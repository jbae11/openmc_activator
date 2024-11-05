import numpy as np
import openmc.deplete
import openmc
import os, tempfile


class OpenmcActivator:


    unit_dict = {'mass': 'grams', 
                 'decay_heat': 'watts',
                 'activity': 'becquerels',
                  # 'gamma_spec': '1/s'
                }

    def __init__(self,ebins,mg_flux, temperature=294,
                openmc_chain_file=None):

        assert(len(ebins) == len(mg_flux)+1)
        self.ebins = np.array(ebins)
        # check ascending (low to high)
        assert(np.all(ebins[:-1] < ebins[1:]))
        self.mg_flux = np.array(mg_flux)

        self.chain_file = self._resolve_file_path(openmc_chain_file, 'chain')
        self.chain = openmc.deplete.Chain.from_xml(self.chain_file)
        self.nuclides = [q.name for q in self.chain.nuclides]
        self.norm_flux = self.mg_flux / sum(self.mg_flux)
        self.micro_xs = openmc.deplete.MicroXS.from_multigroup_flux(
            energies=self.ebins,
            multigroup_flux=list(self.norm_flux),
            temperature=temperature,
            chain_file=self.chain_file,
            **{'output': False}
        )


    def _resolve_file_path(self, fp, which):
        key_dict = {'chain': 'chain_file',
                    'xs_data': 'cross_sections'
                    }
        assert(which in key_dict), 'Invalid `which`'
        key = key_dict[which]
        if not fp:
            if key in openmc.config:
                return openmc.config[key]
            else:
                raise ValueError("Either provide filename or set openmc.config['%s']" %key)
        else:
            assert(os.path.exists(fp)), 'Filepath %s does not exist' %fp
            return fp


    def activate(self,
                 material,
                 source_rate_list,
                 timesteps,
                 metric_list: list=['mass'],
                 split_irr=None,
                 reduce_chain_level=5,
                 timestep_units='d',
                 result_path=None
                ):
        # check material
        assert(material.volume) # cc

        if split_irr:
            # to check
            tot_days = sum(days_list)
            tot_fluence = sum(np.array(days_list) * np.array(source_rate_list))
            assert(isinstance(split_irr, int))
            new_days_list = []
            new_source_rate_list = []
            for sr, day in zip(source_rate_list, days_list):
                if sr == 0:
                    new_source_rate_list.append(sr)
                    new_days_list.append(day)
                else:
                    new_day = day / split_irr
                    for i in range(split_irr):
                        new_days_list.append(new_day)
                        new_source_rate_list.append(sr)
            
            new_tot_days = sum(new_days_list)
            new_fluence = sum(np.array(new_days_list) * np.array(new_source_rate_list))
            assert(np.isclose(new_fluence, tot_fluence, rtol=1e-4)), print(new_fluence, tot_fluence)
            assert(np.isclose(new_tot_days, tot_days, rtol=1e-4)), print(new_tot_days, tot_days)

            days_list = new_days_list
            source_rate_list = new_source_rate_list


        operator = openmc.deplete.IndependentOperator(
            materials=openmc.Materials([material]),
            #fluxes=[self.norm_flux*material.volume],
            fluxes=[material.volume],
            # fluxes=[1],
            micros=[self.micro_xs],
            normalization_mode='source-rate',
            reduce_chain=bool(reduce_chain_level),
            reduce_chain_level=reduce_chain_level
        )
        integrator = openmc.deplete.PredictorIntegrator(
            operator=operator,
            timesteps=timesteps,
            source_rates=source_rate_list,
            timestep_units=timestep_units
        )


        # if result path is none, make a temp file that gets deleted after
        if not result_path:
            remove = True
            # generate temporary filepath
            tmpfile = 'tmp.h5'
            while os.path.exists(tmpfile):
                tmpfile = 't' + tmpfile
            result_path = tmpfile
        else:
            remove = False

        integrator.integrate(path=result_path, output=False)

        return read_output(result_path, self.nuclides, metric_list, timesteps, material.id,
                           timestep_units, remove)


def read_output(output_path:str, nuclides, metric_list:list, timesteps:list, material_id:str,
                timestep_units:str, remove:bool=False):

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

