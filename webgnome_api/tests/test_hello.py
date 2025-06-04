"""
tests for the hello view
"""
from .base import FunctionalTestBase

# importing views.hello directly is breaking other tests ???
# maybe because it's running code before initializing the views?
# from webgnome_api.views import hello


class TestHello(FunctionalTestBase):
    '''
    Tests the hello page
    '''
    def test_hello(self):
        resp = self.testapp.get('/')
        resp = resp.unicode_body.strip()

        # just to check while testing
        # open("home.html", 'w', encoding='utf-8').write(resp)

        assert "<h1>WebGnome API Server Package Versions</h1>" in resp
        assert resp.startswith("<html>")
        assert resp.endswith("</html>")

        # some of the table entries
        assert "webgnome_api" in resp
        assert "gnome" in resp
        assert "libgoods" in resp
        assert ("adios-db" in resp) or ("adios_db" in resp)
        assert "pynucos" in resp

    def test_get_pkg_info_table1(self):
        from webgnome_api.views import hello
        table = hello.get_pkg_info_table('gnome')

        print(table)
        assert "<td>gnome</td>" in table

    def test_get_pkg_info_table2(self):
        from webgnome_api.views import hello

        table = hello.get_pkg_info_table('webgnome_api')

        print(table)
        assert "<td>webgnome_api</td>" in table
