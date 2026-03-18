"""
Views for help documentation
"""
from os import walk
from os.path import sep, join, isfile, isdir

from datetime import datetime, timezone
import time
import logging

import urllib.parse
import base64

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import ujson
import redis

from docutils.core import publish_parts

from cornice import Service
from pyramid.httpexceptions import (HTTPError,
                                    HTTPNotFound,
                                    HTTPBadRequest,
                                    HTTPUnauthorized)

from google.auth.transport.requests import Request
from google.auth.exceptions import GoogleAuthError, ClientCertError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from webgnome_api.common.views import cors_exception, cors_policy
from webgnome_api.common.indexing import iter_keywords

log = logging.getLogger(__name__)

help_svc = Service(name='help', path='/help*dir',
                   description="Help Documentation and Feedback API",
                   cors_policy=cors_policy)


@help_svc.get()
def get_help(request):
    """
    Get the requested help file if it exists
    """
    help_dir = get_help_dir_from_config(request)
    requested_dir = urllib.parse.unquote(sep.join(request.matchdict['dir']))
    requested_file = join(help_dir, requested_dir)

    if isfile(requested_file + '.rst'):
        # a single help file was requested
        html = ''
        with open(requested_file + '.rst', 'r', encoding="utf-8") as f:
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
                with open(join(path, fname), 'r', encoding="utf-8") as f:
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
                    with open(join(path, fname), 'r', encoding="utf-8") as f:
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
    """
    Creates a feedback entry for the given help section
    """
    try:
        json_request = ujson.loads(request.body)
    except Exception as e:
        raise cors_exception(request, HTTPBadRequest) from e

    json_request['ts'] = int(time.time())

    # save_feedback_to_redis(request, json_request)

    try:
        save_feedback_to_smtp(request, json_request)
    except GoogleAuthError as e:
        raise cors_exception(
            request,
            HTTPUnauthorized,
            explanation=f'{e}'
        ) from e

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
    """
    save our feedback to smtp
    """
    body = generate_email_body(json_request)
    attachment = generate_email_attachment(json_request)

    if 'index' in json_request:
        subject = f"WebGnomeAPI feedback: {json_request['index']}"
    else:
        subject = 'WebGnomeAPI feedback'

    settings = request.registry.settings
    oauth_creds = settings.get('oauth_credentials', {})
    sender = settings.get('help.smtp.sender', 'developer@noaa.gov')
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

    return save_msg_with_gmail_api(msg, sender, oauth_creds, recipients)


def generate_email_body(json_request):
    """Generate our e-mail body from the request info"""
    ts_datetime = datetime.fromtimestamp(json_request['ts'], tz=timezone.utc)
    json_request['ts'] = f"{json_request['ts']} ({ts_datetime})"

    resp = ''

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
    """Generate our e-mail attachment from the request info"""
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


def save_msg_with_gmail_api(msg, sender, oauth_creds, recipients):
    """
    Save message using the gmail api

    Note: The credentials have been generated for a particular
          Gmail user, and the sender probably needs to match.
    """
    _check_credentials(oauth_creds)
    creds = _get_credentials_obj(oauth_creds)

    try:
        with build('gmail', 'v1', credentials=creds) as service:
            create_message = {
                'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()
            }

            res = service.users().messages().send(
                userId="me",
                body=create_message,
            ).execute()
            log.info('sent message to %s', res)
    except HTTPError as e:
        log.info('An error occurred: %s', e)
        log.info('sender: %s, recipients: %s', sender, recipients)


def _check_credentials(oauth_creds):
    msgs = []
    for k in ['client_id',
              'client_secret',
              'refresh_token',
              'scopes',
              'token',
              'token_uri']:
        if k not in oauth_creds:
            msgs.append(f'Credential attribute {k} is missing')

    if len(msgs) > 0:
        raise ClientCertError(code=535, msg=';'.join(msgs))


def _get_credentials_obj(oauth_creds):
    """Uses the refresh token to obtain a new, short-lived access token"""
    credentials = Credentials(**oauth_creds)

    # Force a refresh to get a new access token
    credentials.refresh(Request())

    return credentials

def _get_access_token(oauth_creds):
    return _get_credentials_obj(oauth_creds).token


def _get_sasl_oauth_string(email_user, access_token):
    """
    Creates the standardized SASL XOAUTH2 string for SMTP authentication.
    """
    auth_string = f'user={email_user}\x01auth=Bearer {access_token}\x01\x01'
    return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')


def get_help_dir_from_config(request):
    """Get help dir from config"""
    help_dir = request.registry.settings['help_dir']

    if help_dir[0] == sep:
        full_path = help_dir
    else:
        here = request.registry.settings['install_path']
        full_path = join(here, help_dir)

    return full_path
