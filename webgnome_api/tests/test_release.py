"""
Functional tests for the Gnome Release object Web API
"""
import pytest
import webtest
from .base import FunctionalTestBase


class ReleaseTests(FunctionalTestBase):
    '''
        Tests out the Gnome Release object API
    '''
    req_data = {'obj_type': 'gnome.spills.release.PointLineRelease',
                }

    options_headers = {# 'Origin': 'http://0.0.0.0:8080',
                       # this needs to match cors_policy.origins in config-test.ini
                       'Origin': 'http://0.0.0.0:9999',
                       'Access-Control-Request-Method': 'GET'}


    def test_options(self):
        '''
            TODO: Maybe testing the options should be in a separate
                  module that covers the options for all entry points.
            ?? - is this testing any "options" other than CORS access??

            TODO: another test to make sure that access fails if the request comes
                  from somewhere else.
        '''
        resp = self.testapp.options('/release',
                                    headers=self.options_headers)
        resp_methods = set(resp.headers['Access-Control-Allow-Methods']
                           .lower().split(','))
        assert resp_methods == {'get', 'head', 'options', 'post', 'put'}

    def test_cors_no_access(self):
        '''
        Check that if the request comes from somethign not on the list
        that it fails.
        '''
        headers = {'Origin': 'http://0.0.0.0:1111',
                   'Access-Control-Request-Method': 'GET'}
        with pytest.raises(webtest.app.AppError) as err:
            resp = self.testapp.options('/release',
                                        headers=headers)
        assert 'Bad response: 400 Bad Request' in err.value.args[0]

    def test_get_no_id(self):
        resp = self.testapp.get('/release')

        assert 'obj_type' in self.req_data
        obj_type = self.req_data['obj_type'].split('.')[-1]

        assert (obj_type, obj_type) in [(name, obj['obj_type'].split('.')[-1])
                                        for name, obj
                                        in resp.json_body.items()]

    def test_get_invalid_id(self):
        obj_id = 0xdeadbeef
        self.testapp.get('/release/{0}'.format(obj_id), status=404)

    def test_post_no_payload(self):
        self.testapp.post_json('/release', status=400)

    def test_put_no_payload(self):
        self.testapp.put_json('/release', status=400)

    def test_put_no_id(self):
        self.testapp.put_json('/release', params=self.req_data, status=404)

    def test_put_invalid_id(self):
        params = {}
        params.update(self.req_data)
        params['id'] = str(0xdeadbeef)

        self.testapp.put_json('/release', params=params, status=404)

    def perform_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        json_obj['num_elements'] = 100

    def check_updates(self, json_obj):
        '''
            We can overload this function when subclassing our tests
            for new object types.
        '''
        assert json_obj['num_elements'] == 100


class PointLineReleaseTests(ReleaseTests):
    '''
        Tests out the Gnome Release object API
    '''
    req_data = {
                'obj_type': 'gnome.spills.release.PointLineRelease',
                'num_elements': 100,
                'num_released': 0,
                'release_time': '2014-04-15T13:22:20.930570',
                'start_time_invalid': True,
                'end_release_time': '2014-04-15T13:22:20.930570',
                'end_position': (28.0, -78.0, 0.0),
                'start_position': (28.0, -78.0, 0.0),
                }

    def test_get_valid_id(self):
        # 1. create the object by performing a put with no id
        # 2. get the valid id from the response
        # 3. perform an additional get of the object with a valid id
        # 4. check that our new JSON response matches the one from the create
        resp1 = self.testapp.post_json('/release', params=self.req_data)

        obj_id = resp1.json_body['id']
        resp2 = self.testapp.get('/release/{0}'.format(obj_id))

        for k in ('id', 'obj_type'):
            assert resp2.json_body[k] == resp1.json_body[k]

    def test_put_valid_id(self):
        # 1. create the object by performing a put with no id
        # 2. get the valid id from the response
        # 3. update the properties in the JSON response
        # 4. update the object by performing a put with a valid id
        # 5. check that our new properties are in the new JSON response
        resp = self.testapp.post_json('/release', params=self.req_data)

        req_data = resp.json_body
        self.perform_updates(req_data)

        resp = self.testapp.put_json('/release', params=req_data)
        self.check_updates(resp.json_body)

    def perform_updates(self, json_obj):
        super(PointLineReleaseTests, self).perform_updates(json_obj)
        json_obj['start_position'] = (100.0, 100.0, 0.0)
        json_obj['end_position'] = (50.0, 50.0, 10.0)

    def check_updates(self, json_obj):
        super(PointLineReleaseTests, self).check_updates(json_obj)
        assert all([i == j
                    for i, j in zip(json_obj['start_position'],
                                    (100.0, 100.0, 0.0))
                    ])

        assert all([i == j
                    for i, j in zip(json_obj['end_position'],
                                    (50.0, 50.0, 10.0))
                    ])


class BasicReleaseTests(ReleaseTests):
    '''
        Tests out the Gnome Spatial Release object API
    '''
    req_data = {'obj_type': 'gnome.spills.release.Release',
                'name': 'Release',
                'release_time': '2014-08-02T21:20:50',
                'custom_positions': [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
                }

    def test_get_valid_id(self):
        # 1. create the object by performing a put with no id
        # 2. get the valid id from the response
        # 3. perform an additional get of the object with a valid id
        # 4. check that our new JSON response matches the one from the create
        resp = self.testapp.post_json('/release', params=self.req_data)
        rel1 = resp.json_body

        obj_id = rel1['id']
        resp = self.testapp.get('/release/{0}'.format(obj_id))
        rel2 = resp.json_body

        for k in ('id', 'obj_type'):
            assert rel1[k] == rel2[k]

    def test_put_valid_id(self):
        # 1. create the object by performing a put with no id
        # 2. get the valid id from the response
        # 3. update the properties in the JSON response
        # 4. update the object by performing a put with a valid id
        # 5. check that our new properties are in the new JSON response
        resp = self.testapp.post_json('/release', params=self.req_data)

        req_data = resp.json_body
        self.perform_updates(req_data)

        resp = self.testapp.put_json('/release', params=req_data)
        self.check_updates(resp.json_body)

    def perform_updates(self, json_obj):
        json_obj['custom_positions'] = [[100.0, 100.0, 0.0],
                                      [100.0, 100.0, 0.0]]

    def check_updates(self, json_obj):
        assert all([i == j
                    for i, j in zip(json_obj['custom_positions'],
                                    [[100.0, 100.0, 0.0],
                                     [100.0, 100.0, 0.0]]
                                    )
                    ])
