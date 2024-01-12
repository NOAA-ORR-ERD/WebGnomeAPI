"""
Functional tests for the Model Web API
"""
# from gnome.multi_model_broadcast import ModelBroadcaster
from .base import FunctionalTestBase, MODELS_DIR

from pprint import PrettyPrinter
pp = PrettyPrinter(indent=2)


class ModelTests(FunctionalTestBase):
    req_data = {'obj_type': 'gnome.model.Model',
                'cache_enabled': False,
                'duration': 86400.0,
                'start_time': '2014-04-09T15:00:00',
                'time_step': 900.0,
                'uncertain': False,
                'weathering_substeps': 1,
                'environment': [],
                'movers': [],
                'outputters': [],
                'spills': [],
                'weatherers': [],
                }

    def test_get_model_no_id(self):
        resp = self.testapp.get('/model')
        specs = resp.json_body

        assert 'id' in specs['Model']
        for k in ('id', 'start_time', 'time_step', 'duration',
                  'cache_enabled', 'uncertain', 'map',
                  'environment', 'spills', 'movers', 'weatherers'):
            assert k in specs['Model']
        # what other kinds of validation should we have here?

    def test_get_model_no_id_active(self):
        '''
            Here we test the get with no ID, but where an active model
            is attached to the session.
        '''
        resp = self.testapp.post_json('/model')
        model1 = resp.json_body

        resp = self.testapp.get('/model')
        model2 = resp.json_body

        assert model1['id'] == model2['id']

    def test_get_model_invalid_id(self):
        obj_id = 0xdeadbeef
        self.testapp.get('/model/{0}'.format(obj_id), status=404)

    def test_get_model_invalid_id_active(self):
        '''
            Here we test the get with an invalid ID, but where an active model
            is attached to the session.
        '''
        self.testapp.get('/model')

        obj_id = 0xdeadbeef
        self.testapp.get('/model/{0}'.format(obj_id), status=404)

    def test_get_model_valid_id(self):
        resp = self.testapp.post_json('/model')
        model1 = resp.json_body

        resp = self.testapp.get('/model/{0}'.format(model1['id']))
        model2 = resp.json_body

        assert model1['id'] == model2['id']

    def test_post_no_payload(self):
        '''
            This case is different than the other object create methods.
            We would like to be able to post with no payload and receive
            a newly created 'blank' Model.
        '''
        resp = self.testapp.post_json('/model')
        model1 = resp.json_body

        for k in ('id', 'start_time', 'duration',
                  'cache_enabled', 'uncertain', 'map',
                  'environment', 'spills', 'movers', 'weatherers'):
            assert k in model1

        # we should not have any adios uncertainty models if we
        # have no weathering.
        # Note: We are choosing to skip this feature for now, and the only
        #       way to do that here is to comment out the assert.
        # app = self.testapp.app
        # assert not [v
        #             for s in list(app.registry.settings['objects'].values())
        #             for v in list(s.values())
        #             if isinstance(v, ModelBroadcaster)]

    def test_post_no_payload_twice(self):
        resp = self.testapp.post_json('/model')
        model1 = resp.json_body

        resp = self.testapp.post_json('/model')
        model2 = resp.json_body

        assert model1['id'] != model2['id']

    def test_post_with_payload_no_map(self):
        resp = self.testapp.post_json('/model', params=self.req_data)
        model1 = resp.json_body

        assert 'map' in model1

    def test_post_with_payload_none_map(self):
        req_data = self.req_data.copy()
        req_data['map'] = None

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'map' in model1

    def test_put_no_payload(self):
        self.testapp.put_json('/model', status=400)

    def test_put_no_id_no_active_model(self):
        self.testapp.put_json('/model', params=self.req_data, status=404)

    def test_put_no_id_active_model(self):
        resp = self.testapp.post_json('/model', params=self.req_data)

        model1 = resp.json_body
        model1['time_step'] = 1800.0

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['time_step'] == 1800.0

    def test_put_valid_id(self):
        resp = self.testapp.post_json('/model', params=self.req_data)

        model1 = resp.json_body
        model1['time_step'] = 1800.0

        resp = self.testapp.put_json('/model', params=model1)

        model2 = resp.json_body
        assert model2['time_step'] == 1800.0

        # we should not have any adios uncertainty models if we
        # have no weathering
        # Note: We are choosing to skip this feature for now, and the only
        #       way to do that here is to comment out the assert.
        # app = self.testapp.app
        # assert not [v
        #             for s in list(app.registry.settings['objects'].values())
        #             for v in list(s.values())
        #             if isinstance(v, ModelBroadcaster)]


class NestedModelTests(FunctionalTestBase):
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

    def test_post_with_nested_map(self):
        req_data = self.req_data.copy()
        req_data['map'] = {'obj_type': 'gnome.maps.map.MapFromBNA',
                           'filename': str(MODELS_DIR / 'Test.bna'),
                           'refloat_halflife': 1.0
                           }

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'filename' in model1['map']
        assert 'refloat_halflife' in model1['map']

    def test_put_with_nested_map(self):
        req_data = self.req_data.copy()
        req_data['map'] = {'obj_type': 'gnome.maps.map.MapFromBNA',
                           'filename': str(MODELS_DIR / 'Test.bna'),
                           'refloat_halflife': 1.0
                           }

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        model1['map']['refloat_halflife'] = 2.0

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['map']['refloat_halflife'] == 2.0

    def test_post_with_nested_environment(self):
        req_data = self.req_data.copy()
        req_data['environment'] = [{'obj_type': 'gnome.environment.Wind',
                                    'description': 'Wind Object',
                                    'updated_at': '2014-03-26T14:52:45.385126',
                                    'source_type': 'undefined',
                                    'source_id': 'undefined',
                                    'timeseries': [('2012-11-06T20:10:30',
                                                    (1.0, 0.0)),
                                                   ('2012-11-06T20:15:30',
                                                    (1.0, 270.0))],
                                    'units': 'meter per second'
                                    }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'environment' in model1
        assert model1['environment'][0]['obj_type'] == ('gnome.environment'
                                                        '.wind.Wind')
        assert 'description' in model1['environment'][0]
        assert 'timeseries' in model1['environment'][0]
        assert 'units' in model1['environment'][0]

    def test_put_with_nested_environment(self):
        req_data = self.req_data.copy()
        req_data['environment'] = [{'obj_type': 'gnome.environment.Wind',
                                    'description': 'Wind Object',
                                    'updated_at': '2014-03-26T14:52:45.385126',
                                    'source_type': 'undefined',
                                    'source_id': 'undefined',
                                    'timeseries': [('2012-11-06T20:10:30',
                                                    (1.0, 0.0)),
                                                   ('2012-11-06T20:15:30',
                                                    (1.0, 270.0))],
                                    'units': 'meter per second'
                                    }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        model1['environment'][0]['units'] = 'knots'

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['environment'][0]['units'] == 'knots'

    def test_put_environment_inside_model(self):
        req_data = self.req_data.copy()
        req_data['environment'] = [{'obj_type': 'gnome.environment.Wind',
                                    'description': 'Wind Object',
                                    'updated_at': '2014-03-26T14:52:45.385126',
                                    'source_type': 'undefined',
                                    'source_id': 'undefined',
                                    'timeseries': [('2012-11-06T20:10:30',
                                                    (1.0, 0.0)),
                                                   ('2012-11-06T20:15:30',
                                                    (1.0, 270.0))],
                                    'units': 'meter per second'
                                    }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        environment = model1['environment'][0]
        environment['units'] = 'knots'

        resp = self.testapp.put_json('/environment', params=environment)
        environment2 = resp.json_body

        assert environment2['units'] == 'knots'

        # we should not have any adios uncertainty runs yet
        # Note: We are choosing to skip this feature for now, and the only
        #       way to do that here is to comment out the assert.
        # app = self.testapp.app
        # assert not [v
        #             for s in list(app.registry.settings['objects'].values())
        #             for v in list(s.values())
        #             if isinstance(v, ModelBroadcaster)]

    def test_put_with_sparse_environment(self):
        '''
            Sparse means that we have a previously created object (Wind),
            and we update the model using just the obj_type and the id.
        '''
        req_data = self.req_data.copy()
        wind_data = {'obj_type': 'gnome.environment.Wind',
                     'description': 'Wind Object',
                     'updated_at': '2014-03-26T14:52:45.385126',
                     'source_type': 'undefined',
                     'source_id': 'undefined',
                     'timeseries': [('2012-11-06T20:10:30',
                                     (1.0, 0.0)),
                                    ('2012-11-06T20:15:30',
                                     (1.0, 270.0))],
                     'units': 'meter per second'
                     }

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        resp = self.testapp.post_json('/environment', params=wind_data)
        wind1 = resp.json_body

        model1['environment'].append({'obj_type': wind1['obj_type'],
                                      'id': wind1['id']
                                      }
                                     )
        pp.pprint(model1)

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['environment'][0]['units'] == 'meter per second'

    def test_post_with_nested_mover(self):
        req_data = self.req_data.copy()
        req_data['movers'] = [{'obj_type': ('gnome.movers.c_wind_movers'
                                            '.PointWindMover'),
                               'active_range': ('-inf', 'inf'),
                               'on': True,
                               'uncertain_angle_scale': 0.4,
                               'uncertain_duration': 3.0,
                               'uncertain_speed_scale': 2.0,
                               'uncertain_time_delay': 0.0,
                               'wind': {'obj_type': 'gnome.environment.Wind',
                                        'description': 'Wind Object',
                                        'updated_at': '2014-03-26T14:52:45.39',
                                        'source_type': 'undefined',
                                        'source_id': 'undefined',
                                        'units': 'meter per second',
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
                                        }
                               }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'movers' in model1
        assert model1['movers'][0]['obj_type'] == ('gnome.movers.c_wind_movers'
                                                   '.PointWindMover')
        assert 'active_range' in model1['movers'][0]
        assert 'on' in model1['movers'][0]
        assert 'uncertain_angle_scale' in model1['movers'][0]
        assert 'uncertain_duration' in model1['movers'][0]
        assert 'uncertain_speed_scale' in model1['movers'][0]
        assert 'uncertain_time_delay' in model1['movers'][0]
        assert 'description' in model1['movers'][0]['wind']
        assert 'updated_at' in model1['movers'][0]['wind']
        assert 'source_type' in model1['movers'][0]['wind']
        assert 'source_id' in model1['movers'][0]['wind']
        assert 'timeseries' in model1['movers'][0]['wind']
        assert 'units' in model1['movers'][0]['wind']

    def test_put_with_nested_mover(self):
        req_data = self.req_data.copy()
        req_data['movers'] = [{'obj_type': ('gnome.movers.c_wind_movers'
                                            '.PointWindMover'),
                               'active_range': ('-inf', 'inf'),
                               'on': True,
                               'uncertain_angle_scale': 0.4,
                               'uncertain_duration': 3.0,
                               'uncertain_speed_scale': 2.0,
                               'uncertain_time_delay': 0.0,
                               'wind': {'obj_type': 'gnome.environment.Wind',
                                        'description': 'Wind Object',
                                        'updated_at': '2014-03-26T14:52:45.39',
                                        'source_type': 'undefined',
                                        'source_id': 'undefined',
                                        'units': 'meter per second',
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
                                        }
                               }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        model1['movers'][0]['wind']['units'] = 'knots'

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['movers'][0]['wind']['units'] == 'knots'

    def test_put_with_nested_sparse_wind_mover(self):
        req_data = self.req_data.copy()
        req_data['movers'] = [{'obj_type': ('gnome.movers.c_wind_movers'
                                            '.PointWindMover'),
                               'active_range': ('-inf', 'inf'),
                               'on': True,
                               'uncertain_angle_scale': 0.4,
                               'uncertain_duration': 3.0,
                               'uncertain_speed_scale': 2.0,
                               'uncertain_time_delay': 0.0,
                               'wind': {'obj_type': 'gnome.environment.Wind',
                                        'description': 'Wind Object',
                                        'updated_at': '2014-03-26T14:52:45.39',
                                        'source_type': 'undefined',
                                        'source_id': 'undefined',
                                        'units': 'meter per second',
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
                                        }
                               }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        # create a sparse mover
        mover = dict([(k, v)
                      for k, v in model1['movers'][0].items()
                      if k in ('id', 'obj_type')])
        model1['movers'][0] = mover

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['movers'][0]['wind']['units'] == 'meter per second'

    def test_put_with_nested_sparse_random_mover(self):
        req_data = self.req_data.copy()
        req_data['movers'] = [{'obj_type': ('gnome.movers.random_movers'
                                            '.RandomMover'),
                               'name': 'RandomMover',
                               'active_range': ('-inf', 'inf'),
                               'on': True,
                               'diffusion_coef': 100000.0,
                               'uncertain_factor': 2.0
                               }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        # create a sparse mover
        mover = dict([(k, v)
                      for k, v in model1['movers'][0].items()
                      if k in ('id', 'obj_type')])
        model1['movers'][0] = mover

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['movers'][0]['diffusion_coef'] == 100000.0

    def test_put_with_nested_sparse_random_mover_3d(self):
        req_data = self.req_data.copy()
        req_data['movers'] = [{'obj_type': ('gnome.movers.random_movers'
                                            '.RandomMover3D'),
                               'name': 'RandomMover3D',
                               'active_range': ('-inf', 'inf'),
                               'on': True,
                               'mixed_layer_depth': 10.0,
                               'vertical_diffusion_coef_above_ml': 5.0,
                               'vertical_diffusion_coef_below_ml': 0.11
                               }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        # create a sparse mover
        mover = dict([(k, v)
                      for k, v in model1['movers'][0].items()
                      if k in ('id', 'obj_type')])
        model1['movers'][0] = mover

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['movers'][0]['mixed_layer_depth'] == 10.0

    def test_put_with_nested_sparse_cats_mover(self):
        req_data = self.req_data.copy()
        req_data['movers'] = [{'obj_type': 'gnome.movers.c_current_movers.CatsMover',
                               'filename': str(MODELS_DIR / 'tidesWAC.CUR'),
                               'scale': True,
                               'scale_value': 1.0,
                               'tide': {'obj_type': 'gnome.environment.Tide',
                                        'filename': str(MODELS_DIR / 'CLISShio.txt'),
                                        },
                               }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        # create a sparse mover
        mover = dict([(k, v)
                      for k, v in model1['movers'][0].items()
                      if k in ('id', 'obj_type')])
        model1['movers'][0] = mover

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['movers'][0]['tide']['filename'] == 'CLISShio.txt'

    def test_post_with_nested_weatherer(self):
        req_data = self.req_data.copy()

        req_data['weatherers'] = [{'obj_type': 'gnome.weatherers.Evaporation',
                                   'active_range': ('-inf', 'inf'),
                                   'on': True,
                                   }]

        req_data['outputters'] = [{'obj_type': ('gnome.outputters.weathering'
                                                '.WeatheringOutput'),
                                   'name': 'WeatheringOutput',
                                   'output_last_step': True,
                                   'output_zero_step': True}]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'weatherers' in model1
        assert model1['weatherers'][0]['obj_type'] == ('gnome.weatherers'
                                                       '.evaporation'
                                                       '.Evaporation')
        assert 'active_range' in model1['weatherers'][0]
        assert 'on' in model1['weatherers'][0]

    def test_put_with_nested_weatherer(self):
        req_data = self.req_data.copy()
        req_data['weatherers'] = [{'obj_type': 'gnome.weatherers.Evaporation',
                                   'active_range': ('-inf', 'inf'),
                                   'on': True,
                                   }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        model1['weatherers'][0]['on'] = False

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['weatherers'][0]['on'] is False

    def test_put_with_added_weatherer(self):
        req_data = self.req_data.copy()
        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        weatherer = {'obj_type': 'gnome.weatherers.Evaporation',
                     'active_range': ('-inf', 'inf'),
                     'on': True,
                     }
        resp1 = self.testapp.post_json('/weatherer', params=weatherer)
        weatherer = resp1.json_body

        model1['weatherers'] = [weatherer]

        outputter = {'obj_type': ('gnome.outputters.weathering'
                                  '.WeatheringOutput'),
                     'name': 'WeatheringOutput',
                     'output_last_step': True,
                     'output_zero_step': True}

        resp1 = self.testapp.post_json('/outputter', params=outputter)
        outputter = resp1.json_body

        model1['outputters'] = [outputter]

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['weatherers'][0]['on'] is True

    def test_put_with_removed_weatherer(self):
        req_data = self.req_data.copy()
        req_data['weatherers'] = [{'obj_type': 'gnome.weatherers.Evaporation',
                                   'active_range': ('-inf', 'inf'),
                                   'on': True,
                                   }]

        req_data['outputters'] = [{'obj_type': ('gnome.outputters.weathering'
                                                '.WeatheringOutput'),
                                   'name': 'WeatheringOutput',
                                   'output_last_step': True,
                                   'output_zero_step': True}]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'weatherers' in model1
        assert model1['weatherers'][0]['obj_type'] == ('gnome.weatherers'
                                                       '.evaporation'
                                                       '.Evaporation')
        assert 'active_range' in model1['weatherers'][0]
        assert 'on' in model1['weatherers'][0]

        model1['weatherers'] = []

        resp = self.testapp.post_json('/model', params=model1)
        model1 = resp.json_body

    def test_put_weatherer_inside_model(self):
        req_data = self.req_data.copy()
        req_data['environment'] = [{'obj_type': 'gnome.environment.Wind',
                                    'description': 'Wind Object',
                                    'updated_at': '2014-03-26T14:52:45.385126',
                                    'source_type': 'undefined',
                                    'source_id': 'undefined',
                                    'timeseries': [('2012-11-06T20:10:30',
                                                    (1.0, 0.0)),
                                                   ('2012-11-06T20:15:30',
                                                    (1.0, 270.0))],
                                    'units': 'meter per second'
                                    }]
        req_data['weatherers'] = [{'obj_type': 'gnome.weatherers.Evaporation',
                                   'active_range': ('-inf', 'inf'),
                                   'on': True,
                                   }]

        req_data['outputters'] = [{'obj_type': ('gnome.outputters.weathering'
                                                '.WeatheringOutput'),
                                   'name': 'WeatheringOutput',
                                   'output_last_step': True,
                                   'output_zero_step': True}]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        weatherer = model1['weatherers'][0]
        weatherer['on'] = False

        resp = self.testapp.put_json('/weatherer', params=weatherer)
        weatherer = resp.json_body

        assert weatherer['on'] is False

        weatherer = model1['weatherers'][0]
        weatherer['on'] = True

        resp = self.testapp.put_json('/weatherer', params=weatherer)
        weatherer = resp.json_body

        assert weatherer['on'] is True

    def test_post_with_nested_outputter(self):
        req_data = self.req_data.copy()
        req_data['outputters'] = [{'obj_type': ('gnome.outputters.renderer'
                                                '.Renderer'),
                                   'name': 'Renderer',
                                   'output_last_step': True,
                                   'output_zero_step': True,
                                   'draw_ontop': 'forecast',
                                   'map_filename': str(MODELS_DIR / 'Test.bna'),
                                   'output_dir': str(MODELS_DIR / 'images'),
                                   'image_size': [800, 600],
                                   'viewport': [[-71.22429878, 42.18462639],
                                                [-70.41468719, 42.63295739]]
                                   }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'outputters' in model1
        assert model1['outputters'][0]['obj_type'] == ('gnome.outputters'
                                                       '.renderer.Renderer')
        assert 'name' in model1['outputters'][0]
        assert 'output_last_step' in model1['outputters'][0]
        assert 'output_zero_step' in model1['outputters'][0]
        assert 'draw_ontop' in model1['outputters'][0]
        assert 'map_filename' in model1['outputters'][0]
        assert 'output_dir' in model1['outputters'][0]
        assert 'image_size' in model1['outputters'][0]
        assert 'viewport' in model1['outputters'][0]

    def test_put_with_nested_outputter(self):
        req_data = self.req_data.copy()
        req_data['outputters'] = [{'obj_type': ('gnome.outputters.renderer'
                                                '.Renderer'),
                                   'name': 'Renderer',
                                   'output_last_step': True,
                                   'output_zero_step': True,
                                   'draw_ontop': 'forecast',
                                   'map_filename': str(MODELS_DIR / 'Test.bna'),
                                   'output_dir': str(MODELS_DIR / 'images'),
                                   'image_size': [800, 600],
                                   'viewport': [[-71.22429878, 42.18462639],
                                                [-70.41468719, 42.63295739]]
                                   }]

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        model1['outputters'][0]['output_last_step'] = False

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['outputters'][0]['output_last_step'] is False

    def test_create_model_then_add_wind(self):
        req_wind_data = {'obj_type': 'gnome.environment.Wind',
                         'description': 'Wind Object',
                         'updated_at': '2014-03-26T14:52:45.385126',
                         'source_type': 'undefined',
                         'source_id': 'undefined',
                         'timeseries': [('2012-11-06T20:10:30', (1.0, 0.0)),
                                        ('2012-11-06T20:15:30', (1.0, 270.0))],
                         'units': 'meter per second'
                         }

        print('creating model...')
        resp = self.testapp.post_json('/model', params=self.req_data)
        model1 = resp.json_body

        print('creating wind...')
        resp = self.testapp.post_json('/environment', params=req_wind_data)
        wind_data = resp.json_body

        model1['environment'] = [{'obj_type': wind_data['obj_type'],
                                  'id': wind_data['id'],
                                  'name': 'Custom Wind',
                                  'units': 'meter per second'
                                  }]

        print('updating model with sparse existing wind...')
        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['environment'][0]['id'] == wind_data['id']
        assert model2['environment'][0]['name'] == 'Custom Wind'

        resp = self.testapp.get('/model')
        model3 = resp.json_body

        assert model3['environment'][0]['id'] == wind_data['id']
        assert model3['environment'][0]['name'] == 'Custom Wind'

    def test_create_model_then_replace_wind(self):
        req_wind_data = {'obj_type': 'gnome.environment.Wind',
                         'description': 'Wind Object',
                         'updated_at': '2014-03-26T14:52:45.385126',
                         'source_type': 'undefined',
                         'source_id': 'undefined',
                         'timeseries': [('2012-11-06T20:10:30', (1.0, 0.0)),
                                        ('2012-11-06T20:15:30', (1.0, 270.0))],
                         'units': 'meter per second'
                         }

        print('creating model...')
        resp = self.testapp.post_json('/model', params=self.req_data)
        model1 = resp.json_body

        print('creating wind...')
        resp = self.testapp.post_json('/environment', params=req_wind_data)
        wind_data = resp.json_body

        model1['environment'] = [{'obj_type': wind_data['obj_type'],
                                  'id': wind_data['id'],
                                  'name': 'Custom Wind',
                                  'units': 'meter per second'
                                  }]

        print('updating model with sparse existing wind...')
        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['environment'][0]['id'] == wind_data['id']
        assert model2['environment'][0]['name'] == 'Custom Wind'

        resp = self.testapp.get('/model')
        model3 = resp.json_body

        assert model3['environment'][0]['id'] == wind_data['id']
        assert model3['environment'][0]['name'] == 'Custom Wind'

        print('creating new wind...')
        resp = self.testapp.post_json('/environment', params=req_wind_data)
        wind2_data = resp.json_body

        model3['environment'] = [{'obj_type': wind2_data['obj_type'],
                                  'id': wind2_data['id'],
                                  'name': 'Custom Wind 2',
                                  'units': 'meter per second'
                                  }]

        print('\nwind_data id:', wind_data['id'])
        print('wind2_data id:', wind2_data['id'])
        print('updating model with new existing wind...')
        resp = self.testapp.put_json('/model', params=model3)
        model4 = resp.json_body

        assert model4['environment'][0]['id'] == wind2_data['id']
        assert model4['environment'][0]['name'] == 'Custom Wind 2'

    def test_post_with_nested_spill(self):
        req_data = self.req_data.copy()
        spill_data = [{'obj_type': 'gnome.spills.spill.Spill',
                       'name': 'What a Name',
                       'on': True,
                       'release': {'obj_type': ('gnome.spills.release'
                                                '.PointLineRelease'),
                                   'name': 'PointLineRelease',
                                   'num_elements': 1000,
                                   'release_time': '2013-02-13T09:00:00',
                                   'end_release_time': '2013-02-13T15:00:00',
                                   'start_position': [144.664166, 13.441944,
                                                      0.0],
                                   'end_position': [144.664166, 13.441944,
                                                    0.0],
                                   },
                       'substance': {'obj_type': 'gnome.spills.substance.NonWeatheringSubstance',
                                     'windage_range': [0.01, 0.04],
                                     'windage_persist': 900,
                                     },
                       }]
        req_data['spills'] = spill_data

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        assert 'spills' in model1
        assert model1['spills'][0]['obj_type'] == ('gnome.spills.spill.Spill')

        assert 'name' in model1['spills'][0]
        assert 'on' in model1['spills'][0]
        assert 'release' in model1['spills'][0]
        assert 'substance' in model1['spills'][0]

        assert 'name' in model1['spills'][0]['release']
        assert 'num_elements' in model1['spills'][0]['release']
        assert 'release_time' in model1['spills'][0]['release']
        assert 'end_release_time' in model1['spills'][0]['release']
        assert 'start_position' in model1['spills'][0]['release']
        assert 'end_position' in model1['spills'][0]['release']

        assert 'windage_range' in model1['spills'][0]['substance']

    def test_put_with_nested_spill(self):
        req_data = self.req_data.copy()
        spill_data = [{'obj_type': 'gnome.spills.spill.Spill',
                       'name': 'What a Name',
                       'on': True,
                       'release': {'obj_type': ('gnome.spills.release'
                                                '.PointLineRelease'),
                                   'name': 'PointLineRelease',
                                   'num_elements': 1000,
                                   'release_time': '2013-02-13T09:00:00',
                                   'end_release_time': '2013-02-13T15:00:00',
                                   'start_position': [144.664166, 13.441944,
                                                      0.0],
                                   'end_position': [144.664166, 13.441944,
                                                    0.0],
                                   },
                       'substance': {'obj_type': 'gnome.spills.substance.NonWeatheringSubstance',
                                     'initializers': [{'obj_type': 'gnome.spills.initializers.InitWindages',
                                                       'windage_range': [0.01, 0.04],
                                                       'windage_persist': 900,
                                                       }
                                                      ]
                                     },
                       }]
        req_data['spills'] = spill_data

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        model1['spills'][0]['on'] = False
        model1['spills'][0]['release']['num_elements'] = 2000

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['spills'][0]['on'] is False
        assert model2['spills'][0]['release']['num_elements'] == 2000

        resp = self.testapp.get('/model')
        model3 = resp.json_body

        assert model3['spills'][0]['on'] is False
        assert model3['spills'][0]['release']['num_elements'] == 2000

    def test_put_with_nested_sparse_spill(self):
        req_data = self.req_data.copy()
        spill_data = [{'obj_type': 'gnome.spills.spill.Spill',
                       'name': 'What a Name',
                       'on': True,
                       'release': {'obj_type': ('gnome.spills.release'
                                                '.PointLineRelease'),
                                   'name': 'PointLineRelease',
                                   'num_elements': 1000,
                                   'release_time': '2013-02-13T09:00:00',
                                   'end_release_time': '2013-02-13T15:00:00',
                                   'start_position': [144.664166, 13.441944,
                                                      0.0],
                                   'end_position': [144.664166, 13.441944,
                                                    0.0],
                                   },
                       'substance': {'obj_type': 'gnome.spills.substance.NonWeatheringSubstance',
                                     'initializers': [{'obj_type': 'gnome.spills.initializers.InitWindages',
                                                       'windage_range': [0.01, 0.04],
                                                       'windage_persist': 900,
                                                       }]
                                     },
                       }]
        req_data['spills'] = spill_data

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        # create a sparse spill
        spill = dict([(k, v)
                      for k, v in model1['spills'][0].items()
                      if k in ('id', 'obj_type')])
        model1['spills'][0] = spill

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['spills'][0]['on']
        assert model2['spills'][0]['release']['num_elements'] == 1000

    def test_put_with_remove_spill(self):
        req_data = self.req_data.copy()
        spill_data = [{'obj_type': 'gnome.spills.spill.Spill',
                       'name': 'What a Name',
                       'on': True,
                       'release': {'obj_type': ('gnome.spills.release'
                                                '.PointLineRelease'),
                                   'name': 'PointLineRelease',
                                   'num_elements': 1000,
                                   'release_time': '2013-02-13T09:00:00',
                                   'end_release_time': '2013-02-13T15:00:00',
                                   'start_position': [144.664166, 13.441944,
                                                      0.0],
                                   'end_position': [144.664166, 13.441944,
                                                    0.0],
                                   },
                       'substance': {'obj_type': 'gnome.spills.substance.NonWeatheringSubstance',
                                     'initializers': [{'obj_type': 'gnome.spills.initializers.InitWindages',
                                                       'windage_range': [0.01, 0.04],
                                                       'windage_persist': 900,
                                                       }]
                                     },
                       }]
        req_data['spills'] = spill_data

        resp = self.testapp.post_json('/model', params=req_data)
        model1 = resp.json_body

        model1['spills'][0]['on'] = False
        model1['spills'][0]['release']['num_elements'] = 2000

        resp = self.testapp.put_json('/model', params=model1)
        model2 = resp.json_body

        assert model2['spills'][0]['on'] is False
        assert model2['spills'][0]['release']['num_elements'] == 2000

        resp = self.testapp.get('/model')
        model3 = resp.json_body

        assert model3['spills'][0]['on'] is False
        assert model3['spills'][0]['release']['num_elements'] == 2000

        model3['spills'] = []
        resp = self.testapp.put_json('/model', params=model3)
        model4 = resp.json_body

        assert len(model4['spills']) == 0
