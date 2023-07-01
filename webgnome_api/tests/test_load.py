"""
Functional tests for the Gnome Location object Web API
"""
import zipfile

import pytest

from gnome.model import Model

from .base import FunctionalTestBase, MODELS_DIR


TEST_SAVEFILE = str(MODELS_DIR / "long_island_sound.gnome")
TEST_UPLOAD_SAVEFILE = str(MODELS_DIR / "SaveModel.gnome")


def compare_savefiles(sfile1, sfile2):
    """
    Compare two save files to see if they are the same

    Used for the test of loading a save file

    This is a bit tricky as the unique ids will NOT be the same

    But the easist way to do it is to load them both into gnome,
    and then check if the models are equal

    Maybe something more complex in the future?
    """
    model1 = Model.load_savefile(sfile1)
    model2 = Model.load_savefile(sfile2)

    return model1 == model2


class LoadModelTest(FunctionalTestBase):
    '''
    Tests out the Gnome Location object API
    '''
    def test_file_upload(self):
        resp = self.testapp.get('/model')
        model = resp.json_body

        for c in ('environment', 'map',
                  'movers', 'outputters', 'spills', 'weatherers'):
            assert model['Model'][c] is None

        field_name = 'new_model'
        file_name = TEST_SAVEFILE

        self.testapp.post('/upload', {'session': '1234'},
                          upload_files=[(field_name, file_name,)]
                          )

        resp = self.testapp.get('/model')
        model = resp.json_body

        for c in ('environment', 'map',
                  'movers', 'outputters', 'spills', 'weatherers'):
            assert model[c] is not None

    def test_file_download(self):
        # first we load the model from our zipfile.
        field_name = 'new_model'
        test_file = TEST_SAVEFILE
        save_file = TEST_UPLOAD_SAVEFILE

        resp = self.testapp.post_json('/session')
        req_session = resp.json_body['id']

        self.testapp.post('/upload', {'session': req_session},
                          upload_files=[(field_name, test_file,)]
                          )

        resp = self.testapp.get('/model')
        model = resp.json_body

        for c in ('environment', 'map', 'movers', 'outputters',
                  'spills', 'weatherers'):
            assert model[c] is not None

        # next, we download the model as a zipfile.
        resp = self.testapp.get('/download')

        with open(save_file, 'wb') as file_:
            file_.write(resp.body)

        assert zipfile.is_zipfile(save_file)

        assert compare_savefiles(test_file, save_file)
