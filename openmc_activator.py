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
        # check ascending
        assert(np.all(ebins[:-1] < ebins[1:]))
        self.mg_flux = np.array(mg_flux)

        self.chain_file = self._resolve_file_path(openmc_chain_file, 'chain')

        self.norm_flux = self.mg_flux / sum(self.mg_flux)
        self.micro_xs = openmc.deplete.MicroXS.from_multi_group_flux(
            energies=self.ebins,
            multi_group_flux=list(self.norm_flux),
            temperature=temperature,
            chain_file=self.chain_file
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
                 days_list,
                 metric_list: list=['mass'],
                 split_irr=None,
                 reduce_chain_level=5
                ):
        # check material
        assert(material.volume) # cc
        density = material.get_mass_density() # g/cc
        mass = material.volume * material.density

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
            timesteps=days_list,
            source_rates=source_rate_list,
            timestep_units='d'
        )

        #! something smart with tempfiles
        integrator.integrate()

        results = openmc.deplete.ResultsList.from_hdf5('depletion_results.h5')

        # get metrics
        metric_dict = {metric: {'meta_days': [0] + list(days_list)} for metric in metric_list}
        # add all the isos
        tmp_mat = results[0].get_material(str(material.id))
        nuclides = [nuc.name for nuc in tmp_mat.nuclides]
        for metric in metric_list:
            metric_dict[metric]['meta_total'] = []
            for iso in nuclides:
                metric_dict[metric][iso] = []

        for result in results:
            mat = result.get_material(str(material.id))
            if 'mass' in metric_dict:
                tot = 0
                for iso in nuclides:
                    mass = mat.get_mass(iso)
                    tot += mass
                    metric_dict['mass'][iso].append(mass)
                metric_dict['mass']['meta_total'].append(tot)
            if 'decay_heat' in metric_dict:
                td = mat.get_decay_heat('W', by_nuclide=True)
                for k,v in td.items():
                    metric_dict['decay_heat'][k].append(v)
                metric_dict['decay_heat']['meta_total'].append(sum(td.values()))

            if 'activity' in metric_dict:
                td = mat.get_activity('Bq', by_nuclide=True)
                for k,v in td.items():
                    metric_dict['activity'][k].append(v)
                metric_dict['activity']['meta_total'].append(sum(td.values()))

        return metric_dict

