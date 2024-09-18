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
        print(resp)

        """
        <html>
          <body>
            <h1>WebGnome API Server Package Versions</h1>
            <p>
            <table>
              <tr><th>webgnome_api</th></tr>
              <tr><td>name:</td><td>webgnome_api</td></tr>
              <tr><td>version:</td><td>0.9</td></tr>
              <tr><td>author:</td><td>ADIOS/GNOME team at NOAA ORR</td></tr>
            </table>
            </p>
            <p>
            <table>
              <tr><th>pygnome</th></tr>
              <tr><td>name:</td><td>pyGnome</td></tr>
              <tr><td>version:</td><td>1.1.7</td></tr>
              <tr><td>author:</td><td>Gnome team at NOAA/ORR/ERD</td></tr>
            </table>
            </p>
          </body>
        </html>
        """

        assert "<h1>WebGnome API Server Package Versions</h1>" in resp
        assert resp.startswith("<html>")
        assert resp.endswith("</html>")

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
