"""
Views for help documentation
"""
from os import walk
from os.path import sep, join, isfile, isdir

from datetime import datetime, timezone
import time
import logging

import urllib.parse
import smtplib
from smtplib import SMTPAuthenticationError

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import ujson
import redis

from docutils.core import publish_parts

from cornice import Service
from pyramid.httpexceptions import (HTTPNotFound,
                                    HTTPBadRequest,
                                    HTTPUnauthorized)

from webgnome_api.common.views import cors_exception, cors_policy
from webgnome_api.common.indexing import iter_keywords

log = logging.getLogger(__name__)

help_svc = Service(name='help', path='/help*dir',
                   description="Help Documentation and Feedback API",
                   cors_policy=cors_policy)


@help_svc.get()
def get_help(request):
    '''Get the requested help file if it exists'''
    help_dir = get_help_dir_from_config(request)
    requested_dir = urllib.parse.unquote(sep.join(request.matchdict['dir']))
    requested_file = join(help_dir, requested_dir)

    if isfile(requested_file + '.rst'):
        # a single help file was requested
        html = ''
        with open(requested_file + '.rst', 'r') as f:
            html = publish_parts(f.read(), writer_name='html')['html_body']

        return {'path': requested_file, 'html': html}
    elif isdir(requested_file) and requested_dir != '':
        # a directory was requested
        # aggregate the files contained with in the given directory
        # and sub dirs.
        for path, _dirnames, filenames in walk(requested_file):
            filenames.sort()

            html = ''

            for fname in filenames:
                with open(join(path, fname), 'r') as f:
                    html += publish_parts(f.read(),
                                          writer_name='html')['html_body']

            return {'path': requested_file, 'html': html}
    elif isdir(requested_file) and requested_dir == '':
        # all helps requested
        aggregate = []
        for path, _dirnames, filenames in walk(requested_file):
            filenames.sort()

            # exclude location file user guides
            if path.count(join('model', 'locations')) == 0:
                for fname in filenames:
                    text = ''
                    with open(join(path, fname), 'r') as f:
                        text = f.read()

                    parts_whole = publish_parts(text)
                    parts = publish_parts(text, writer_name='html')

                    html = parts['html_body']
                    keywords = iter_keywords(parts_whole['whole'])

                    aggregate.append({'path': join(path,
                                                   fname.replace('.rst', '')),
                                      'html': html,
                                      'keywords': keywords})

        return aggregate
    else:
        raise cors_exception(request, HTTPNotFound)


@help_svc.put()
@help_svc.post()
def create_help_feedback(request):
    '''Creates a feedback entry for the given help section'''
    try:
        json_request = ujson.loads(request.body)
    except Exception:
        raise cors_exception(request, HTTPBadRequest)

    json_request['ts'] = int(time.time())

    # save_feedback_to_redis(request, json_request)

    try:
        save_feedback_to_smtp(request, json_request)
    except SMTPAuthenticationError as e:
        raise cors_exception(request, HTTPUnauthorized,
                             explanation=f'{e}')

    return json_request


def save_feedback_to_redis(request, json_request):
    """
    Deprecated in favor of e-mailing the feedback
    """
    rhost = request.registry.settings.get('redis.sessions.host', 'localhost')
    rport = request.registry.settings.get('redis.sessions.port', 6379)

    client = redis.Redis(host=rhost, port=rport)

    if 'index' not in json_request:
        json_request['index'] = client.incr('index')

    client.set('feedback' + str(json_request['index']), str(json_request))


def save_feedback_to_smtp(request, json_request):
    body = generate_email_body(json_request)
    attachment = generate_email_attachment(json_request)

    if 'index' in json_request:
        subject = f'WebGnomeAPI feedback: {json_request['index']}'
    else:
        subject = 'WebGnomeAPI feedback'

    settings = request.registry.settings
    sender = settings.get('help.smtp.sender', 'developer@noaa.gov')
    password = settings.get('help.smtp.password', 'no password')
    recipients = settings.get(
        'help.smtp.recipients',
        'developer@noaa.gov'
    ).split('\n')

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg.attach(body)
    msg.attach(attachment)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())


def generate_email_body(json_request):
    resp = ''

    ts_datetime = datetime.fromtimestamp(json_request['ts'], tz=timezone.utc)
    json_request['ts'] = f'{json_request['ts']} ({ts_datetime})'

    for k in ['id', 'path', 'ts', 'index', 'helpful', 'response']:
        v = json_request.get(k, 'None')
        resp += f'<b>{k}</b>: {v}<br>\n'

    return MIMEText(
        '<html>\n'
        '  <body>\n'
        f'    {resp}\n'
        '  <body>\n'
        '<html>\n',
        'html'
    )


def generate_email_attachment(json_request):
    content = f"{json_request.get('html', 'None')}<br>"

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(
        '<html>\n'
        '  <body>\n'
        f'    {content}\n'
        '  <body>\n'
        '<html>\n'
    )

    encoders.encode_base64(part)

    part.add_header('Content-Disposition',
                    'attachment; filename= help_form.html')

    return part


def get_help_dir_from_config(request):
    help_dir = request.registry.settings['help_dir']

    if help_dir[0] == sep:
        full_path = help_dir
    else:
        here = request.registry.settings['install_path']
        full_path = join(here, help_dir)

    return full_path
