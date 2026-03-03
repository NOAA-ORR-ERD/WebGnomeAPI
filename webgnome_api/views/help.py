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
import base64
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
                                    HTTPUnauthorized,
                                    HTTPInternalServerError)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

import pdb
from pprint import pprint

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
    except Exception:
        raise cors_exception(request, HTTPBadRequest)

    json_request['ts'] = int(time.time())

    # save_feedback_to_redis(request, json_request)

    try:
        save_feedback_to_smtp(request, json_request)
    except SMTPAuthenticationError as e:
        raise cors_exception(request, HTTPUnauthorized, explanation=f'{e}')

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

    save_msg_with_gmail_api(msg, "oauth2_credentials.json")


def save_msg_with_gmail_api(msg, credentials_filename):
    """save message using the gmail api"""
    with open(credentials_filename, encoding="utf-8") as file:
        config = ujson.load(file)

    try:
        web_cfg = config["web"]
    except KeyError as e:
        raise HTTPInternalServerError(
            "OAUTH_CONFIG JSON must contain a top-level 'web' key"
        ) from e
    # logging.info('web_cfg: %s', web_cfg)

    scopes = ["https://www.googleapis.com/auth/gmail.send"]
    redirect_uri = web_cfg.get("redirect_uris", [None])[0]
    if redirect_uri is None:
        raise HTTPInternalServerError(
            "No redirect URI available"
        )
    logging.info('redirect_uri: %s', redirect_uri)

    flow = Flow.from_client_config(config, scopes=scopes)
    flow.redirect_uri = redirect_uri

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    logging.info('Open this URL in a browser and authorize: %s', auth_url)
    logging.info('After approval, paste either the full redirect URL '
                 'or the "code" parameter value.')


# import smtplib
# import base64
# from email.mime.text import MIMEText

# # Assume you have already obtained an OAuth2 access token
# # (This step typically involves using specific libraries like google-auth-oauthlib)
# access_token = "YOUR_OAUTH2_ACCESS_TOKEN"
# user_email = "your-email@gmail.com"
# recipient_email = "recipient@example.com"

# def generate_oauth2_string(username, token):
#     """Generates an RFC 68ietf-rfc-6801 SASL XOAUTH2 authentication string."""
#     auth_string = f"user={username}\x01auth=Bearer {token}\x01\x01"
#     return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

# # Email content
# msg = MIMEText('This is the body of the email.')
# msg['Subject'] = 'Test Email via OAuth2'
# msg['From'] = user_email
# msg['To'] = recipient_email

# # Connect to the SMTP server and authenticate
# try:
#     server = smtplib.SMTP('smtp.gmail.com', 587)
#     server.ehlo()
#     server.starttls()
#     server.ehlo()
    
#     # Authenticate using XOAUTH2
#     auth_string_encoded = generate_oauth2_string(user_email, access_token)
#     server.authenticate('XOAUTH2', lambda x: auth_string_encoded)
    
#     # Send the email
#     server.sendmail(user_email, recipient_email, msg.as_string())
#     print("Email sent successfully!")
    
# except smtplib.SMTPException as e:
#     print(f"Error: {e}")

# finally:
#     server.quit()


def generate_email_body(json_request):
    resp = ''

    ts_datetime = datetime.fromtimestamp(json_request['ts'], tz=timezone.utc)
    json_request['ts'] = f"{json_request['ts']} ({ts_datetime})"

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


def generate_oauth2_string(username, token):
    """Generates an RFC 68ietf-rfc-6801 SASL XOAUTH2 authentication string."""
    auth_string = f"user={username}\x01auth=Bearer {token}\x01\x01"
    return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')


def get_help_dir_from_config(request):
    help_dir = request.registry.settings['help_dir']

    if help_dir[0] == sep:
        full_path = help_dir
    else:
        here = request.registry.settings['install_path']
        full_path = join(here, help_dir)

    return full_path
