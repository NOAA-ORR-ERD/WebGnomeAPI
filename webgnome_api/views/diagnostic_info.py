"""
The base URI for our server.
"""
from pyramid.response import Response
from cornice import Service

diagnostic = Service(
    name='diagnostic',
    path='/diagnostic',
    description="Diagnosic information of our server environment"
)


@diagnostic.get()
def get_diagnostic_info(request):
    """Returns diagnosic information of our server environment in html."""

    body = ('<html>'
            '    <body>'
            '        <h1>WebGnome API Server Environmental Information</h1>'
            '         <p>'
            'Warning: get rid of this when we are done debugging the help feedback.'
            '         </p>'
            '         <p>'
            f'{get_server_environmental_info(request)}'
            '         </p>'
            '    </body>'
            '</html>'
            )

    response = Response(content_type='text/html', body=body)

    return response


def get_server_environmental_info(request):
    """
    Get server environment
    """
    return to_table(['Key', 'Value'], request.environ.items())


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
