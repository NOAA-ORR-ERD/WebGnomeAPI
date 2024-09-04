"""
The base URI for our server.
"""
import importlib.metadata
from pyramid.response import Response
from cornice import Service

hello = Service(name='hello', path='/', description="Introduction")


@hello.get()
def get_package_info_response(request):
    """Returns Package Version Information in html."""

    body = ('<html>'
            '    <body>'
            '        <h1>WebGnome API Server Package Versions</h1>'
            f'         <p>{get_pkg_info_table("webgnome_api")}</p>'
            f'         <p>{get_pkg_info_table("gnome")}</p>'
            f'         <p>{get_pkg_info_table("libgoods")}</p>'
            f'         <p>{get_pkg_info_table("adios_db")}</p>'
            f'         <p>{get_pkg_info_table("pynucos")}</p>'
            # f'       <h1>Conda Packages</h1>'
            # f'         {get_conda_packages()}\n'
            '    </body>'
            '</html>'
            )

    response = Response(content_type='text/html', body=body)

    return response


def get_pkg_info_table(package):
    """
    Updated to use importlib.metadata
    """
    header_fields = [package]
    try:
        msg_dict = importlib.metadata.metadata(package).json

        rows = []
        # for k in ('Name', 'Version', 'Branch', 'LastUpdate', 'Author'):
        for k in ('name', 'version', 'author'):
            if k in msg_dict:
                rows.append([k + ':', msg_dict[k]])
    except  importlib.metadata.PackageNotFoundError:
        rows = [[f"name: {package}"], ["version: not installed"], ["author: unknown"]]


    return to_table(header_fields, rows)


def to_table(header_items, row_items):
    header = to_table_row(header_items, header=True)
    rows = ''.join([to_table_row(r) for r in row_items])

    return '<table>{}{}</table>'.format(header, rows)


def to_table_row(items, header=False):
    if header is True:
        return f'<tr>{"".join([to_table_header(i) for i in items])}</tr>'
    else:
        return f'<tr>{"".join([to_table_data(i) for i in items])}</tr>'


def to_table_header(item):
    return '<th>{}</th>'.format(item)


def to_table_data(item):
    return '<td>{}</td>'.format(item)

def get_conda_packages():
    # neither of tehse work -- conda not installed
    # there should be a way to make sure we have a package listing available though.
    # try:
    #     import conda.cli.python_api as capi
    #     pkgs, _, _ = capi.run_command('list')
    # except ImportError:
    #     pkgs = "conda not installed on the server"
    import subprocess
    pkgs = subprocess.run("conda list", capture_output=True)

    html = f"<pre>\n{pkgs}\n</pre>"
    return html

