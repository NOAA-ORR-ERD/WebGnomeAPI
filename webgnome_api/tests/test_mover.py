"""
Functional tests for the Mover Web API
"""
import time
import pytest
from .base import FunctionalTestBase, MODELS_DIR


class BaseMoverTests(FunctionalTestBase):
    '''
    Tests out the Gnome Mover common APIs
    '''
    req_data = {'obj_type': 'gnome.movers.simple_mover.SimpleMover',
                'uncertainty_scale': 0.5,
                'velocity': (1.0, 1.0, 1.0)
                }

    def test_get_no_id(self):
        resp = self.testapp.get('/mover')

        assert 'obj_type' in self.req_data
        obj_type = self.req_data['obj_type'].split('.')[-1]

        assert (obj_type, obj_type) in [(name, obj['obj_type'].split('.')[-1])
                                        for name, obj
                                        in resp.json_body.items()]

    def test_get_invalid_id(self):
        obj_id = 0xdeadbeef
        self.testapp.get('/mover/{0}'.format(obj_id), status=404)

    def test_get_valid_id(self):
        # 1. Create the object by performing a put with no id
        # 2. Get the valid id from the response
        # 3. Perform an additional get of the object with a valid id
        # 4. Check that our new JSON response matches the one from the create
        resp1 = self.testapp.post_json('/mover', params=self.req_data)

        obj_id = resp1.json_body['id']
        resp2 = self.testapp.get('/mover/{0}'.format(obj_id))

        for a in ('id', 'obj_type', 'active_range'):
            assert resp2.json_body[a] == resp1.json_body[a]

    def test_post_no_payload(self):
        self.testapp.post_json('/mover', status=400)

    def test_put_no_payload(self):
        self.testapp.put_json('/mover', status=400)

    def test_put_no_id(self):
        self.testapp.put_json('/mover', params=self.req_data, status=404)

    def check_create_properties(self, response):
        for k in ('id', 'obj_type', 'on', 'active_range'):
            assert k in response.json_body


class SimpleMoverTests(BaseMoverTests):
    '''
        Tests out the Gnome Simple Mover API
    '''
    req_data = {'obj_type': 'gnome.movers.simple_mover.SimpleMover',
                'active_range': ('-inf', 'inf'),
                'on': True,
                'uncertainty_scale': 0.5,
                'velocity': (1.0, 1.0, 1.0)
                }

    def test_put_invalid_id(self):
        params = {}
        params.update(self.req_data)
        params['id'] = str(0xdeadbeef)

        self.testapp.put_json('/mover', params=params, status=404)

    def test_put_valid_id(self):
        # 1. create the object by performing a put with no id
        # 2. get the valid id from the response
        # 3. update the properties in the JSON response
        # 4. update the object by performing a put with a valid id
        # 5. check that our new properties are in the new JSON response
        resp = self.testapp.post_json('/mover', params=self.req_data)

        req_data = resp.json_body
        self.perform_updates(req_data)

        resp = self.testapp.put_json('/mover', params=req_data)
        self.check_updates(resp.json_body)

    def check_create_properties(self, response):
        super(SimpleMoverTests, self).check_create_properties(response)

        # specific to SimpleMover()
        assert 'velocity' in response.json_body

    def perform_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        json_obj['velocity'] = [10.0, 10.0, 10.0]
        json_obj['on'] = False

    def check_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        assert json_obj['velocity'] == [10.0, 10.0, 10.0]
        assert json_obj['on'] is False


class WindMoverTests(BaseMoverTests):
    '''
        Tests out the Gnome Wind Mover API
    '''
    wind_req_data = {'obj_type': 'gnome.environment.Wind',
                     'description': 'Wind Object',
                     'updated_at': '2014-03-26T14:52:45.385126',
                     'source_type': 'undefined',
                     'source_id': 'undefined',
                     'timeseries': [('2012-11-06T20:10:30', (1.0, 0.0)),
                                    ('2012-11-06T20:11:30', (1.0, 45.0)),
                                    ('2012-11-06T20:12:30', (1.0, 90.0)),
                                    ('2012-11-06T20:13:30', (1.0, 120.0)),
                                    ('2012-11-06T20:14:30', (1.0, 180.0)),
                                    ('2012-11-06T20:15:30', (1.0, 270.0))],
                     'units': 'meter per second'
                     }

    req_data = {'obj_type': 'gnome.movers.c_wind_movers.PointWindMover',
                'active_range': ('-inf', 'inf'),
                'on': True,
                'uncertain_angle_scale': 0.4,
                'uncertain_angle_units': 'rad',
                'uncertain_duration': 3.0,
                'uncertain_speed_scale': 2.0,
                'uncertain_time_delay': 0.0,
                'wind': None
                }

    def test_get_valid_id(self):
        # 1. create a Wind object
        # 2. create a WindMover object
        # 3. get the WindMover valid id for use in the URL
        # 4. perform an additional get of the object with a valid id
        # 5. check that our new JSON response matches the one from the create
        wind_obj = self.create_wind_obj(self.wind_req_data)
        self.req_data['wind'] = wind_obj

        resp1 = self.testapp.post_json('/mover', params=self.req_data)

        obj_id = resp1.json_body['id']
        resp2 = self.testapp.get('/mover/{0}'.format(obj_id))

        for a in ('id', 'obj_type', 'active_range'):
            assert resp2.json_body[a] == resp1.json_body[a]

        for a in ('uncertain_angle_scale',
                  'uncertain_duration',
                  'uncertain_speed_scale',
                  'uncertain_time_delay'):
            assert resp2.json_body[a] == resp1.json_body[a]

    def test_put_no_id(self):
        # WindMover requires a valid Wind object for creation
        wind_obj = self.create_wind_obj(self.wind_req_data)
        self.req_data['wind'] = wind_obj

        self.testapp.put_json('/mover', params=self.req_data, status=404)

    def test_put_invalid_id(self):
        # WindMover requires a valid Wind object for creation
        wind_obj = self.create_wind_obj(self.wind_req_data)
        self.req_data['wind'] = wind_obj

        params = {}
        params.update(self.req_data)
        params['id'] = str(0xdeadbeef)

        self.testapp.put_json('/mover', params=params, status=404)

    def test_put_valid_id(self):
        # 1. create a Wind object
        # 2. create a WindMover object
        # 3. get the WindMover valid id for use in the URL
        # 3. update the properties in the JSON response
        # 4. update the object by performing a put with a valid id
        # 5. check that our new properties are in the new JSON response

        # WindMover reauires a valid Wind object for creation
        wind_obj = self.create_wind_obj(self.wind_req_data)
        self.req_data['wind'] = wind_obj

        resp = self.testapp.post_json('/mover', params=self.req_data)

        req_data = resp.json_body
        self.perform_updates(req_data)

        resp = self.testapp.put_json('/mover', params=req_data)
        self.check_updates(resp.json_body)

    def create_wind_obj(self, req_data):
        resp = self.testapp.post_json('/environment', params=req_data)
        return resp.json_body

    def check_create_properties(self, response):
        super(WindMoverTests, self).check_create_properties(response)

        # specific to WindMover()
        assert 'uncertain_angle_scale' in response.json_body
        assert 'uncertain_angle_units' in response.json_body
        assert 'uncertain_duration' in response.json_body
        assert 'uncertain_speed_scale' in response.json_body
        assert 'uncertain_time_delay' in response.json_body
        assert 'wind' in response.json_body

    def perform_updates(self, json_obj):
        json_obj['uncertain_duration'] = 2.0
        json_obj['uncertain_speed_scale'] = 3.0
        json_obj['uncertain_time_delay'] = 4.0

    def check_updates(self, json_obj):
        assert json_obj['uncertain_duration'] == 2.0
        assert json_obj['uncertain_speed_scale'] == 3.0
        assert json_obj['uncertain_time_delay'] == 4.0


class RandomMoverTests(BaseMoverTests):
    '''
        Tests out the Gnome Random Mover API
    '''
    req_data = {'obj_type': 'gnome.movers.random_movers.RandomMover',
                'name': 'RandomMover',
                'active_range': ('-inf', 'inf'),
                'on': True,
                'diffusion_coef': 100000.0,
                'uncertain_factor': 2.0
                }

    def test_put_invalid_id(self):
        params = {}
        params.update(self.req_data)
        params['id'] = str(0xdeadbeef)

        self.testapp.put_json('/mover', params=params, status=404)

    def test_put_valid_id(self):
        # 1. create the object by performing a put with no id
        # 2. get the valid id from the response
        # 3. update the properties in the JSON response
        # 4. update the object by performing a put with a valid id
        # 5. check that our new properties are in the new JSON response
        resp = self.testapp.post_json('/mover', params=self.req_data)

        req_data = resp.json_body
        self.perform_updates(req_data)

        resp = self.testapp.put_json('/mover', params=req_data)
        self.check_updates(resp.json_body)

    def check_create_properties(self, response):
        super(SimpleMoverTests, self).check_create_properties(response)

        # specific to SimpleMover()
        assert 'velocity' in response.json_body

    def perform_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        json_obj['diffusion_coef'] = 20000.0
        json_obj['on'] = False

    def check_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        assert json_obj['diffusion_coef'] == 20000.0
        assert json_obj['on'] is False


class RandomMover3DTests(BaseMoverTests):
    '''
        Tests out the Gnome Random Mover 3D API
    '''
    req_data = {'obj_type': 'gnome.movers.random_movers.RandomMover3D',
                'name': 'RandomMover3D',
                'active_range': ('-inf', 'inf'),
                'on': True,
                'mixed_layer_depth': 10.0,
                'vertical_diffusion_coef_above_ml': 5.0,
                'vertical_diffusion_coef_below_ml': 0.11
                }

    def test_put_invalid_id(self):
        params = {}
        params.update(self.req_data)
        params['id'] = str(0xdeadbeef)

        self.testapp.put_json('/mover', params=params, status=404)

    def test_put_valid_id(self):
        resp = self.testapp.post_json('/mover', params=self.req_data)

        req_data = resp.json_body
        self.perform_updates(req_data)

        resp = self.testapp.put_json('/mover', params=req_data)
        self.check_updates(resp.json_body)

        model_id = resp.json_body['id']
        resp = self.testapp.get('/mover/{0}'.format(model_id))
        self.check_updates(resp.json_body)

    def check_create_properties(self, response):
        super(RandomMover3DTests, self).check_create_properties(response)

        # specific to SimpleMover()
        assert 'velocity' in response.json_body

    def perform_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        json_obj['mixed_layer_depth'] = 20.0
        json_obj['vertical_diffusion_coef_above_ml'] = 10.0
        json_obj['vertical_diffusion_coef_below_ml'] = 0.22

    def check_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        assert json_obj['mixed_layer_depth'] == 20.0
        assert json_obj['vertical_diffusion_coef_above_ml'] == 10.0
        assert json_obj['vertical_diffusion_coef_below_ml'] == 0.22


class CatsMoverTests(BaseMoverTests):
    '''
    Tests out the Gnome Cats Mover API
        - Kinda needs a Tide object
    '''
    tide_data = {'obj_type': 'gnome.environment.Tide',
                 'filename': str(MODELS_DIR / 'CLISShio.txt')
                 }

    req_data = {'obj_type': 'gnome.movers.c_current_movers.CatsMover',
                'filename': str(MODELS_DIR / 'tidesWAC.CUR'),
                # 'scale': True, Cannot use any longer due to pygnome changes
                'scale_value': 1.0,
                'scale_refpoint': (-72.705, 41.2275, 0.0),
                }

    def test_put_invalid_id(self):
        params = {}
        params.update(self.req_data)
        params['id'] = str(0xdeadbeef)

        self.testapp.put_json('/mover', params=params, status=404)

    def test_put_valid_id(self):
        req_data = {}
        req_data.update(self.req_data)

        resp = self.testapp.post_json('/environment', params=self.tide_data)
        tide = resp.json_body
        req_data['tide'] = tide

        resp = self.testapp.post_json('/mover', params=req_data)
        mover = resp.json_body

        self.perform_updates(mover)

        resp = self.testapp.put_json('/mover', params=mover)
        self.check_updates(resp.json_body)

        model_id = resp.json_body['id']
        resp = self.testapp.get('/mover/{0}'.format(model_id))
        self.check_updates(resp.json_body)

    def check_create_properties(self, response):
        super(RandomMover3DTests, self).check_create_properties(response)

        # specific to SimpleMover()
        assert 'velocity' in response.json_body

    def perform_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        json_obj['scale_value'] = 2.0
        json_obj['scale_refpoint'] = [-50.0, 50.0, 10.0]

        json_obj['up_cur_uncertain'] = 0.5
        json_obj['down_cur_uncertain'] = -0.5
        json_obj['left_cur_uncertain'] = -0.5
        json_obj['right_cur_uncertain'] = 0.5

        json_obj['uncertain_duration'] = 60.0
        json_obj['uncertain_eddy_diffusion'] = 1.0
        # json_obj['uncertain_eddy_v0'] = 1.0  # failing
        json_obj['uncertain_time_delay'] = 1.0

    def check_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        assert json_obj['scale_value'] == 2.0
        assert json_obj['scale_refpoint'] == [-50.0, 50.0, 10.0]

        assert json_obj['up_cur_uncertain'] == 0.5
        assert json_obj['down_cur_uncertain'] == -0.5
        assert json_obj['left_cur_uncertain'] == -0.5
        assert json_obj['right_cur_uncertain'] == 0.5

        assert json_obj['uncertain_duration'] == 60.0
        assert json_obj['uncertain_eddy_diffusion'] == 1.0
        assert json_obj['uncertain_time_delay'] == 1.0


class CurrentInfoTests(FunctionalTestBase):
    '''
        Tests out the API for getting the current info from the
        current movers in the model.
    '''
    req_data = {'obj_type': 'gnome.model.Model',
                'cache_enabled': False,
                'duration': 86400.0,
                'start_time': '2014-04-09T15:00:00',
                'time_step': 900.0,
                'uncertain': False,
                'weathering_substeps': 1,
                'environment': [],
                'movers': [],
                'weatherers': [],
                'outputters': [],
                'spills': [],
                }
    req_data['movers'] = [{'obj_type': 'gnome.movers.CatsMover',
                           'filename': str(MODELS_DIR / 'tidesWAC.CUR'),
                           'scale': True,
                           'scale_value': 1.0,
                           'tide': {'obj_type': 'gnome.environment.Tide',
                                    'filename': str(MODELS_DIR / 'CLISShio.txt'),
                                    },
                           },
                          {'obj_type': 'gnome.movers.c_wind_movers.PointWindMover',
                           'active_range': ('-inf', 'inf'),
                           'on': True,
                           'uncertain_angle_scale': 0.4,
                           'uncertain_angle_units': 'rad',
                           'uncertain_duration': 3.0,
                           'uncertain_speed_scale': 2.0,
                           'uncertain_time_delay': 0.0,
                           'wind': {'obj_type': 'gnome.environment.Wind',
                                    'description': 'Wind Object',
                                    'updated_at': '2014-03-26T14:52:45.385126',
                                    'source_type': 'undefined',
                                    'source_id': 'undefined',
                                    'timeseries': [('2012-11-06T20:10:30',
                                                    (1.0, 0.0)),
                                                   ('2012-11-06T20:11:30',
                                                    (1.0, 45.0)),
                                                   ('2012-11-06T20:12:30',
                                                    (1.0, 90.0)),
                                                   ('2012-11-06T20:13:30',
                                                    (1.0, 120.0)),
                                                   ('2012-11-06T20:14:30',
                                                    (1.0, 180.0)),
                                                   ('2012-11-06T20:15:30',
                                                    (1.0, 270.0))],
                                    'units': 'meter per second'
                                    }
                           }
                          ]

    def test_get_incomplete_paths(self):
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body

        assert model['movers'][0]['tide']['filename'] == 'CLISShio.txt'

        # step 2: we perform some gets that have incomplete urls
        self.testapp.get('/mover/{0}'.format('current'), status=404)
        self.testapp.get('/mover/{0}/'.format('current'), status=404)
        self.testapp.get('/mover/{0}/{1}'.format('current', 'bogus'),
                         status=404)
        self.testapp.get('/mover/{0}/{1}/'.format('current', 'bogus'),
                         status=404)

    def test_get_complete_path(self):
        '''
            Test the successful retrieval of the current grid
        '''
        begin = time.time()
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body
        print('\n\ngot our model at: ', time.time() - begin)

        assert model['movers'][0]['tide']['filename'] == 'CLISShio.txt'

        # step 2: we perform some gets that have complete urls
        mover_id = model['movers'][0]['id']
        resp = self.testapp.get('/mover/{0}/{1}'.format(mover_id, 'grid'))
        current_info = resp.json_body
        print('\n\ngot our grid at: ', time.time() - begin)

        for r in current_info:
            assert len(r) == 6  # each row contains 3 flattened coordinates

    def test_get_wrong_mover(self):
        '''
            Test the attempt to get a current grid from a mover that is
            not a current mover.
        '''
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body

        assert model['movers'][0]['tide']['filename'] == 'CLISShio.txt'

        # step 2: we perform some gets that have complete urls
        mover_id = model['movers'][1]['id']
        resp = self.testapp.get('/mover/{0}/{1}'.format(mover_id, 'grid'),
                                status=404)


class IceInfoTests(FunctionalTestBase):
    '''
        Tests out the API for getting the ice info from the ice movers
        in the model.
    '''
    movers_data = [{'obj_type': 'gnome.movers.simple_mover.SimpleMover',
                    'name': 'SimpleMover',
                    'active_range': ('-inf', 'inf'),
                    'on': True,
                    'uncertainty_scale': 0.5,
                    'velocity': (1.0, -1.0, 0.0)},
                   {'obj_type': 'gnome.movers.IceMover',
                    'name': 'IceMover',
                    'active_range': ('-inf', 'inf'),
                    'on': True,
                    'current_scale': 1.0,
                    'filename': str(MODELS_DIR / 'acnfs_example.nc'),
                    'topology_file': str(MODELS_DIR / 'acnfs_topo.dat'),
                    'uncertain_along': 0.5,
                    'uncertain_cross': 0.25,
                    'uncertain_duration': 24.0,
                    'uncertain_time_delay': 0.0}]

    outputters_data = [{'obj_type': 'gnome.outputters.IceGeoJsonOutput',
                        'name': 'IceGeoJsonOutput',
                        'on': True,
                        'output_last_step': True,
                        'output_zero_step': True,
                        'ice_movers': [],
                        }]

    spills_data = [{'obj_type': 'gnome.spills.spill.Spill',
                    'name': 'Point Line Release',
                    'on': True,
                    'amount_uncertainty_scale': 0.0,
                    'substance': {'obj_type': 'gnome.spills.substance.NonWeatheringSubstance',
                                  'name': 'NonWeatheringSubstance',
                                  'initializers': [{'obj_type': 'gnome.spills.initializers.InitWindages',
                                                    'name': 'windages',
                                                    'windage_persist': 900,
                                                    'windage_range': (0.01,
                                                                      0.04)
                                                    }],
                                  },
                    'release': {'end_position': (-164.01696, 72.921024, 0.0),
                                'end_release_time': None,
                                'name': 'PointLineRelease',
                                'num_elements': 1,
                                'obj_type': ('gnome.spills.release'
                                             '.PointLineRelease'),
                                'release_time': '2015-05-14T00:00:00',
                                'start_position': (-164.01696, 72.921024, 0.0)}
                    },
                   {'obj_type': 'gnome.spills.spill.Spill',
                    'name': 'Spill',
                    'on': True,
                    'amount_uncertainty_scale': 0.0,
                    'substance': {'obj_type': 'gnome.spills.substance.NonWeatheringSubstance',
                                  'name': 'NonWeatheringSubstance',
                                  'initializers': [{'obj_type': 'gnome.spills.initializers.InitWindages',
                                                    'name': 'windages',
                                                    'windage_persist': 900,
                                                    'windage_range': (0.01,
                                                                      0.04)
                                                    }],
                                  },
                    'release': {'obj_type': ('gnome.spills.release'
                                             '.Release'),
                                'name': 'Release',
                                'release_time': '2015-05-14T00:00:00',
                                'custom_positions': [(-127.1, 47.93, 0.0),
                                                     (-127.033, 47.948, 0.0),
                                                     (-126.967, 47.968, 0.0),
                                                     (-126.9, 47.987, 0.0),
                                                     (-126.833, 48.0056, 0.0),
                                                     (-126.767, 48.024, 0.0),
                                                     (-126.7, 48.043, 0.0),
                                                     (-126.633, 48.062, 0.0),
                                                     (-126.567, 48.081, 0.0),
                                                     (-126.5, 48.1, 0.0)]
                                }
                    }
                   ]

    req_data = {'obj_type': 'gnome.model.Model',
                'name': 'Model',
                'start_time': '2015-05-14T00:00:00',
                'duration': 3600.0,
                'time_step': 900.0,
                'num_time_steps': 5,
                'weathering_substeps': 1,
                'cache_enabled': True,
                'make_default_refs': True,
                'uncertain': True,
                'valid': True,
                'map': {'obj_type': 'gnome.maps.map.MapFromBNA',
                        'name': 'MapBounds_Island.bna',
                        'filename': str(MODELS_DIR / 'MapBounds_Island.bna'),
                        'refloat_halflife': 6.0,
                        'map_bounds': [(-127.465333, 48.3294),
                                       (-126.108847, 48.3294),
                                       (-126.108847, 47.44727),
                                       (-127.465333, 47.44727)],
                        'spillable_area': [((-127.0, 48.1),
                                            (-126.6, 48.1),
                                            (-126.3, 47.8),
                                            (-126.6, 47.6),
                                            (-127.0, 47.6),
                                            (-127.25, 47.8))]
                        },
                'environment': [],
                'weatherers': [],
                'movers': movers_data,
                'spills': spills_data,
                'outputters': [],
                }

    def test_get_incomplete_paths(self):
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body

        assert model['movers'][1]['filename'] == 'acnfs_example.nc'
        assert model['movers'][1]['topology_file'] == 'acnfs_topo.dat'

        # step 2: we perform some gets that have incomplete urls
        self.testapp.get('/mover/{0}'.format('current'), status=404)
        self.testapp.get('/mover/{0}/'.format('current'), status=404)
        self.testapp.get('/mover/{0}/{1}'.format('current', 'bogus'),
                         status=404)
        self.testapp.get('/mover/{0}/{1}/'.format('current', 'bogus'),
                         status=404)

    def test_get_wrong_mover(self):
        '''
            Test the attempt to get a current grid from a mover that is
            not a current mover.
        '''
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body

        assert model['movers'][0]['velocity'] == [1.0, -1.0, 0.0]

        # step 2: we perform some gets that have complete urls
        mover_id = model['movers'][0]['id']
        resp = self.testapp.get('/mover/{0}/{1}'.format(mover_id, 'grid'),
                                status=404)

    @pytest.mark.slow
    def test_get_complete_path(self):
        '''
            Test the successful retrieval of the current grid
        '''
        begin = time.time()
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body
        print('\n\ngot our model at: ', time.time() - begin)

        assert model['movers'][1]['filename'] == 'acnfs_example.nc'
        assert model['movers'][1]['topology_file'] == 'acnfs_topo.dat'

        mover_id = model['movers'][1]['id']
        resp = self.testapp.get('/mover/{0}/{1}'.format(mover_id, 'grid'))
        current_info = resp.json_body
        print('\n\ngot our grid at: ', time.time() - begin)

        for r in current_info:
            assert len(r) == 8  # each row contains 4 flattened coordinates


class CellInfoTests(FunctionalTestBase):
    '''
        Tests out the API for getting the current info from the
        current movers in the model.
    '''
    req_data = {'obj_type': 'gnome.model.Model',
                'cache_enabled': False,
                'duration': 86400.0,
                'start_time': '2014-04-09T15:00:00',
                'time_step': 900.0,
                'uncertain': False,
                'weathering_substeps': 1,
                'environment': [],
                'movers': [],
                'weatherers': [],
                'outputters': [],
                'spills': [],
                }
    req_data['movers'] = [{"obj_type": "gnome.movers.c_GridCurrentMover",
                           "name": "c_GridCurrentMover",
                           "active_range": ('-inf', 'inf'),
                           "on": True,
                           "filename": str(MODELS_DIR / 'ny_cg.nc'),
                           "topology_file": str(MODELS_DIR / 'NYTopology.dat'),
                           "current_scale": 1.0,
                           "uncertain_time_delay": 0.0,
                           "uncertain_duration": 24.0,
                           "uncertain_cross": 0.25,
                           "uncertain_along": 0.5,
                           },
                          {'obj_type': 'gnome.movers.c_wind_movers.PointWindMover',
                           'active_range': ('-inf', 'inf'),
                           'on': True,
                           'uncertain_angle_scale': 0.4,
                           'uncertain_angle_units': 'rad',
                           'uncertain_duration': 3.0,
                           'uncertain_speed_scale': 2.0,
                           'uncertain_time_delay': 0.0,
                           'wind': {'obj_type': 'gnome.environment.Wind',
                                    'description': 'Wind Object',
                                    'updated_at': '2014-03-26T14:52:45.385126',
                                    'source_type': 'undefined',
                                    'source_id': 'undefined',
                                    'timeseries': [('2012-11-06T20:10:30',
                                                    (1.0, 0.0)),
                                                   ('2012-11-06T20:11:30',
                                                    (1.0, 45.0)),
                                                   ('2012-11-06T20:12:30',
                                                    (1.0, 90.0)),
                                                   ('2012-11-06T20:13:30',
                                                    (1.0, 120.0)),
                                                   ('2012-11-06T20:14:30',
                                                    (1.0, 180.0)),
                                                   ('2012-11-06T20:15:30',
                                                    (1.0, 270.0))],
                                    'units': 'meter per second'
                                    }
                           }
                          ]

    def test_get_incomplete_paths(self):
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body

        assert model['movers'][0]['filename'] == 'ny_cg.nc'
        assert model['movers'][0]['topology_file'] == 'NYTopology.dat'

        # step 2: we perform some gets that have incomplete urls
        self.testapp.get('/mover/{0}'.format('current'), status=404)
        self.testapp.get('/mover/{0}/'.format('current'), status=404)
        self.testapp.get('/mover/{0}/{1}'.format('current', 'bogus'),
                         status=404)
        self.testapp.get('/mover/{0}/{1}/'.format('current', 'bogus'),
                         status=404)

    def test_get_complete_path(self):
        '''
            Test the successful retrieval of the current grid
        '''
        begin = time.time()
        params = {}
        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body
        print('\n\ngot our model at: ', time.time() - begin)

        assert model['movers'][0]['filename'] == 'ny_cg.nc'
        assert model['movers'][0]['topology_file'] == 'NYTopology.dat'

        # step 2: we perform some gets that have complete urls
        mover_id = model['movers'][0]['id']
        resp = self.testapp.get('/mover/{0}/{1}'.format(mover_id, 'grid'))
        current_info = resp.json_body
        print('\n\ngot our grid at: ', time.time() - begin)

        for r in current_info:
            assert len(r) == 8  # each row contains 4 flattened coordinates

    def test_get_wrong_mover(self):
        '''
            Test the attempt to get a current grid from a mover that is
            not a current mover.
        '''
        params = {}

        params.update(self.req_data)

        # step 1: we create a model that contains a current mover.
        resp = self.testapp.post_json('/model', params=params)
        model = resp.json_body

        assert model['movers'][0]['filename'] == 'ny_cg.nc'
        assert model['movers'][0]['topology_file'] == 'NYTopology.dat'

        # step 2: we perform some gets that have complete urls
        mover_id = model['movers'][1]['id']
        resp = self.testapp.get('/mover/{0}/{1}'.format(mover_id, 'grid'),
                                status=404)


class PyMoverTests(FunctionalTestBase):
    '''
        Tests out the API for getting the current info from the
        PyMovers in the model.
    '''
    req_data = {'obj_type': 'gnome.movers.py_wind_movers.WindMover',
                'name': 'small_gfs_alaska.nc',
                'filename': str(MODELS_DIR / 'small_gfs_alaska.nc'),
                'wind': {'data_file': str(MODELS_DIR / 'small_gfs_alaska.nc'),
                         'grid_file': str(MODELS_DIR / 'small_gfs_alaska.nc'),
                         'obj_type': ('gnome.environment'
                                      '.environment_objects.GridWind'),
                         'grid': {'obj_type': ('gnome.environment'
                                               '.gridded_objects_base.PyGrid'),
                                  'filename': str(MODELS_DIR / 'small_gfs_alaska.nc')
                                  },
                         'extrapolation_is_allowed': True,
                         },
                }

    def test_get_valid_id(self):
        # 1. create the object by performing a put with no id
        # 2. get the valid id from the response
        # 3. perform an additional get of the object with a valid id
        # 4. check that our new JSON response matches the one from the create
        resp1 = self.testapp.post_json('/mover', params=self.req_data)

        obj_id = resp1.json_body['id']
        resp2 = self.testapp.get('/mover/{0}'.format(obj_id))

        for a in ('id', 'obj_type', 'active_range'):
            assert resp2.json_body[a] == resp1.json_body[a]


# class UploadMoverTests(FunctionalTestBase):
#     '''
#         Tests out the API for uploading a mover

#         It should test for both netcdf and *.cur
#         with and without a time shift
#         and, ideally, a broken netcdf file that can't be written to
#     '''
#     def test_timeshift(self):
#         """
#         test that the timeshifting code works.
#         """
