"""
tests of the "GOODS" functionality

that is, getting maps, currents, etc for the model runs

We really need more tests!

"""
# we're using Unittest Tests, so the pytest-mock fixtures don't work right
from unittest import mock
from pathlib import Path

from .base import FunctionalTestBase, MODELS_DIR

import pytest
import webtest.app

try:
    import libgoods
    # import libgoods.maps
    LIBGOODS = True
    del libgoods
except ModuleNotFoundError:
    LIBGOODS = False


@pytest.mark.skipif(not LIBGOODS, reason="libgoods not there, not testing map access")
class GetMapTest(FunctionalTestBase):
    '''
    Tests of getting a map from the GOODS API

    There should probably be tests of various failing conditions.
    '''

    def test_get_map(self):
        """
        a test of getting a single map

        Note that this does not test if the created file is valid

        That should be tested in the goods / libgoods code.
        """
        # This is what the current request looks like
        # it's passing it on through to GOODS
        # the request should be updated with our "new" API

        # mock the libgoods get_map function
        # if True:
        with mock.patch('libgoods.api.get_map',
                          return_value=("coast.bna", MOCK_MAP)
                          ):

            req_params = {'err_placeholder': '',
                          'NorthLat': 47.06693175688763,
                          'WestLon': -124.26942110656861,
                          'EastLon': -123.6972360021842,
                          'SouthLat': 46.78488364986247,
                          'xDateline': 0,
                          'resolution': 'i',
                          'shoreline': 'GSHHS',
                          'submit': 'Get Map',
                          }

            resp = self.testapp.post('/goods/maps', req_params)

            resp = resp.json_body

            filename = resp[1]
            local_path = Path(resp[0])

            # This might be a bit fragile, but...
            session_id = self.testapp.post('/session').json_body['id']
            expected_path = MODELS_DIR / "session" / session_id / filename
            print(local_path.resolve())
            print(expected_path.resolve())

            # did it put it in the right place?
            assert local_path.resolve() == expected_path.resolve()
            # is there an actual file there?
            assert expected_path.is_file()
            # is it non-empty?
            assert expected_path.stat().st_size > 0

            # maybe check creation time, or ???

@pytest.mark.skipif(not LIBGOODS, reason="libgoods not there, not testing map access")
class GetNWS_WindsTest(FunctionalTestBase):
    '''
    Tests of getting NWS winds from the libGOODS API

    There should probably be tests of various failing conditions.
    '''

    def test_get_NWSwinds(self):
        """
        """

        req_params = {
              'longitude': '-124.8',
              'latitude': '48',
              }

        resp = self.testapp.get('/goods/nws', req_params)

        assert 'timeseries' in resp.json_body

    def test_get_NWSwinds_badlocation(self):
        """
        """

        req_params = {
              'longitude': '0',
              'latitude': '0',
              }

        with self.assertRaises(webtest.app.AppError) as err:
            resp = self.testapp.get('/goods/nws', req_params)


@pytest.mark.skip("not functional right now")
class GetCurrentsTest(FunctionalTestBase):
    '''
    Tests of getting a netcdf file of currents from the webgnomeAPI

    via the libgoods system

    There should probably be tests of various failing conditions.
    '''

    def test_get_current_netcdf(self):
        """
        a test of getting a netcdf file of currents

        """
        # This is what the current request looks like
        # it's passing it on through to GOODS
        # the request should be updated with our "new" API

        req_params = {'err_placeholder': '',
                      'model_name': 'dummy_cur',
                      'NorthLat': 34.0,
                      'WestLon': -119.0,
                      'EastLon': -117.5,
                      'SouthLat': 33.0,
                      'xDateline': 0,
                      'resolution': 'i',
                      'submit': 'Get Map',
                      }

        resp = self.testapp.post('/goods/currents', req_params)

        resp = resp.json_body

        local_path = Path(resp)
        filename = local_path.name

        # This might be a bit fragile, but...
        session_id = self.testapp.post('/session').json_body['id']
        expected_path = MODELS_DIR / "session" / session_id / filename

        # did it put it in the right place?
        local_path = local_path.resolve()
        expected_path = expected_path.resolve()
        assert local_path == expected_path
        # is there an actual file there?
        assert expected_path.is_file()
        # is it non-empty?
        assert expected_path.stat().st_size > 0


class ListModels(FunctionalTestBase):
    """
    Tests of getting a the model list

    Parameters used:

    Query for full list:

map_bounds : [[-360,-85.06],[-360,85.06],[360,85.06],[360,-85.06]]
request_type : ["surface currents"]
1000172761182708.2&map_bounds=%5B%5B-360%2C-85.06%5D%2C%5B-360%2C85.06%5D%2C%5B360%2C85.06%5D%2C%5B360%2C-85.06%5D%5D&request_type=%5B%22surface%20currents%22%5D

map_bounds
[[-360,-85.06],[-360,85.06],[360,85.06],[360,-85.06]]
request_type
["surface winds"]
5542233458021734&map_bounds=%5B%5B-360%2C-85.06%5D%2C%5B-360%2C85.06%5D%2C%5B360%2C85.06%5D%2C%5B360%2C-85.06%5D%5D&request_type=%5B%22surface%20winds%22%5D

One model (LEOFS):
    list_models
    model_id: LEOFS
    model_id=LEOFS

model_id: GFS
model_id=GFS
"""

    # @pytest.mark.parametrize("request_type, bounds", [('["surface currents"]', "[[-360, -85.06], [-360, 85.06], [360, 85.06], [360, -85.06]]"),])
    def test_list_models_surface_currents(self):
        """
        tests getting the metadata of the models

        Only:
         - for surface currents
         - for global map_bounds
        """
        # This is what the current request looks like
        # it's passing it on through to GOODS
        # the request should be updated with our "new" API

        # bounds used for global.
        bounds = "[[-360, -85.06], [-360, 85.06], [360, 85.06], [360, -85.06]]"
        request_type = '["surface currents"]'
        req_params = {
                'map_bounds': bounds,
                'request_type': request_type,
                }
        resp = self.testapp.get('/goods/list_models',
                                req_params)

        resp = resp.json_body

        # should we hard-code what's expected
        print(f"Got {len(resp)} models")
        assert len(resp) > 0, "got zero models!"

        all_expected_keys = {
            'identifier', 'name', 'long_name', 'html_desc', 'regional', 'bounding_box',
            'bounding_poly', 'example_bbox', 'env_params', 'start', 'end', 'actual_start', 'actual_end'
        }
        # just checking that we got what looks like the right dicts.
        for model in resp:
            assert all_expected_keys.issubset(model.keys())

    def test_list_models_surface_winds(self):
        """
        tests getting the metadata of the models

        Only:
         - for surface currents
         - for global map_bounds
        """
        # This is what the current request looks like
        # it's passing it on through to GOODS
        # the request should be updated with our "new" API

        # bounds used for global.
        bounds = "[[-360, -85.06], [-360, 85.06], [360, 85.06], [360, -85.06]]"
        request_type = '["surface winds"]'
        req_params = {
                'map_bounds': bounds,
                'request_type': request_type,
                }
        resp = self.testapp.get('/goods/list_models',
                                req_params)

        resp = resp.json_body
        print(resp)
        # should we hard-code what's expected?
        # as of this test, only one global wind model
        print(f"Got {len(resp)} models")
        assert len(resp) >= 1

        model = resp[0]

        print(f"got: {model['name']}")
        assert model['identifier'] == 'GFS'

        print(f"{model['actual_start']=}")
        print(f"{model['actual_end']=}")

        all_expected_keys = {
            'identifier', 'name', 'long_name', 'html_desc', 'regional', 'bounding_box',
            'bounding_poly', 'example_bbox', 'env_params', 'start', 'end', 'actual_start', 'actual_end'
        }
        # just checking that we got what looks like the right dicts.
        for model in resp:
            assert all_expected_keys.issubset(model.keys())

    def test_list_models_one_model(self):
        """
        list_models is overloaded to return just one model
        if you pass in its ID
        """
        model_id = 'CBOFS'
        req_params = {
                'model_id': model_id
                }
        resp = self.testapp.get('/goods/list_models',
                                req_params)

        meta = resp.json_body

        assert meta['identifier'] == model_id

        all_expected_keys = {
            'identifier', 'name', 'long_name', 'html_desc', 'regional', 'bounding_box',
            'bounding_poly', 'example_bbox', 'env_params', 'start', 'end', 'actual_start', 'actual_end'
        }
        assert all_expected_keys.issubset(meta.keys())

        # actual start and actual end should be populated
        assert meta['actual_start']
        assert meta['actual_end']



MOCK_MAP = \
""""Map Bounds", "2", 4
-124.269421, 46.784884
-124.269421, 47.066932
-123.697236, 47.066932
-123.697236, 46.784884
"2","1",27
-124.106895, 46.784884
-124.138361, 46.905528
-124.110861, 46.915000
-124.089111, 46.894806
-124.094500, 46.869083
-124.043944, 46.857167
-124.063667, 46.863667
-124.050167, 46.890028
-123.999583, 46.903278
-124.008639, 46.914111
-123.875833, 46.942083
-123.806250, 46.971667
-123.834139, 46.961250
-123.947528, 46.968694
-123.915472, 46.977472
-124.013278, 46.984111
-124.028472, 47.029417
-124.120750, 47.041194
-124.151417, 47.021111
-124.126750, 46.950194
-124.159861, 46.946444
-124.150889, 46.932639
-124.173861, 46.927333
-124.176355, 47.066932
-123.697236, 47.066932
-123.697236, 46.784884
-124.106895, 46.784884
"3","1",4
-123.879542, 46.961875
-123.878292, 46.963750
-123.854583, 46.960000
-123.879542, 46.961875
"""
