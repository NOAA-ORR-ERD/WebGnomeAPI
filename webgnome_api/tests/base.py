"""
base.py: Base classes for different types of tests.
"""
import os
import shutil
from pathlib import Path
from unittest import TestCase

from pyramid import testing
from paste.deploy.loadwsgi import appconfig
from webtest import TestApp

from webgnome_api import main

HERE = Path(__file__).parent

MODELS_DIR = HERE.parent.parent / "models"


class GnomeTestCase(TestCase):
    def setUp(self):
        self.project_root = str(HERE.resolve())

    def get_settings(self,
                     config_file='../../config-example.ini#webgnome_api'):
        return appconfig('config:%s' % config_file, relative_to=str(HERE))


class FunctionalTestBase(GnomeTestCase):
    def setUp(self):
        super(FunctionalTestBase, self).setUp()

        self.settings = self.get_settings()
        app = main(None, **self.settings)
        self.testapp = TestApp(app)

        # step 1: We get a session.
        resp = self.testapp.post_json('/session')
        assert 'set-cookie' in resp.headers

    def tearDown(self):
        'Clean up any images the model generated after running tests.'
        test_images_dir = os.path.join(self.settings['model_data_dir'],
                                       'images')
        shutil.rmtree(test_images_dir, ignore_errors=True)

        self.cleanup_web_app_upon_shutdown()

    def cleanup_web_app_upon_shutdown(self):
        '''
        Every test case gets a new instantiated web application,
        and there are some resources that our web application manages
        that need to be cleaned up before the next one gets created.

        It would be nice if pyramid would provide a cleanup method
        upon shutdown.
        '''
        registry = self.testapp.app.registry
        settings = registry.settings

        for session_umodels in settings['uncertain_models'].values():
            print(('our session umodels object:', session_umodels))
            if session_umodels is not None:
                session_umodels.stop()

        settings['redis_pubsub_thread'].stop()

        if hasattr(registry, '_redis_sessions'):
            registry._redis_sessions.connection_pool.disconnect()
        # delete the sessions dir:
        sessions_dir = MODELS_DIR / "session"
        shutil.rmtree(sessions_dir, ignore_errors=True)

    def setup_map_file(self):
        # emulate that the user upload their map file
        # this would put it in their model_data session folder
        session_resp = self.testapp.post('/session')
        (MODELS_DIR / 'session' / session_resp.json_body['id']).mkdir(
            parents=True, exist_ok=True)
        # os.makedirs('./models/session/' + session_resp.json_body['id'])
        shutil.copyfile(MODELS_DIR / 'Test.bna',
                        MODELS_DIR / 'session' / f"{session_resp.json_body['id']}"
                        / "Test.bna")


class UnitTestBase(GnomeTestCase):
    """
    NOTE: this does not seem to be used, and I think is broken
    """
    def setUp(self):
        super(UnitTestBase, self).setUp()

        self.config = testing.setUp()
        self.settings = self.get_settings()

    def tearDown(self):
        testing.tearDown()

    def get_request(self, *args, **kwargs):
        return testing.DummyRequest(*args, **kwargs)

    def get_resource(self, *args, **kwargs):
        return testing.DummyResource(*args, **kwargs)
