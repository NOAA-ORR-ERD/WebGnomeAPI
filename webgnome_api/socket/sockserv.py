import os
import re
import pathlib
import logging
import socketio
import base64
import hashlib
import gevent

log = logging.getLogger(__name__)


def generate_short_session_id(sessid):
    hasher = hashlib.sha1(sessid.encode('utf-8'))
    return base64.urlsafe_b64encode(hasher.digest()).decode()


class WebgnomeSocketioServer(socketio.Server):
    def __init__(self, app_settings=None, api_app=None,
                 **kwargs):
        self.app_settings = app_settings
        self.app = api_app

        cors_origins = (api_app.registry.settings['cors_policy.origins']
                        .split('\n'))

        if '*' in cors_origins:
            cors_origins = '*'  # because ['*'] does not work...

        super(WebgnomeSocketioServer, self).__init__(
            engineio_logger=False,
            cors_allowed_origins=cors_origins,
            **kwargs
        )


class WebgnomeNamespace(socketio.Namespace):
    # req = self.server.app.application.request_factory(environ)
    # req.registry = self.server.app.application.registry
    # can now get session id using req.session.session_id
    # or get_session_objects(request) helper
    #

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sio_sessionid_map = {}
        self.active_greenlets = {}
        self.is_async = True

    def on_connect(self, sid, environ):
        # get request context from the webgnome_api app
        # pdb.set_trace()
        # NOTE: next line will fail if server is restarted and an 'old'
        #       client tries to connect
        # Case for this situation needs to be added.
        # old environ contains old, invalid session_id, this is the problem
        # websocket connection is actually still successful?
        session_id = [s for s in environ['QUERY_STRING'].split('&')
                      if 'session_id' in s][0]
        session_id = session_id.split('=')[1]

        if session_id not in self.server.app.registry.settings['objects']:
            # connection has come in either before the session has been
            # properly established, or an old client socket is attempting to
            # reconnect to a new API
            self.disconnect(sid)
            return False

        sess_hash = generate_short_session_id(session_id)
        lock = gevent.event.Event()
        lock.clear()

        self.save_session(sid, {
            'session_id': session_id,
            'socket_id': sid,
            'session_hash': sess_hash,
            'lock': lock,
            'num_sent': 0,
            'objects': self.server.app.registry.settings['objects'][session_id]
        })

        # Need to map the request session id with the socket id so the
        # Pyramid handler code can get the socket id.
        self.sio_sessionid_map[session_id] = sid

        with self.session(sid) as sock_session:
            self.setup_logger(sock_session)

        return True

    def on_disconnect(self, sid):
        '''
        triggers automatically on webpage closure and refresh
        '''
        with self.session(sid) as sock_session:
            if not sock_session:
                return "session_not_found"

            session_id = sock_session['session_id']
            del self.sio_sessionid_map[session_id]

            if sid in self.active_greenlets:
                self.active_greenlets[sid].kill(block=False)
                del self.active_greenlets[sid]

    # logger handlers below here
    def on_start_logger(self, _sid):
        print("start_logger ack received from client")
        self.emit("logger_started")

    # model run handlers below here
    def on_model_halt(self, sid):
        with self.session(sid) as sock_session:
            log.debug('halting {0}'.format(sock_session['session_hash']))
            sock_session['lock'].clear()

    def on_model_kill(self, sid):  # kill signal from client
        with self.session(sid) as sock_session:
            gl = self.active_greenlets.get(sid)
            if gl:
                log.debug('killing greenlet {0}'.format(gl))
                gl.kill(block=False, timeout=5)
                self.emit('killed', 'Model run terminated', room=sid)
                log.debug('killed greenlet {0}'.format(gl))
                sock_session['num_sent'] = 0
                sock_session['lock'].clear()

    def on_model_isAsync(self, _sid, b):
        self.is_async = bool(b)
        log.debug('setting async to {0}'.format(b))

    def on_model_ack(self, sid, ack):
        with self.session(sid) as sock_session:
            if ack == sock_session['num_sent']:
                sock_session['lock'].set()

            log.debug('ack {0}'.format(ack))

    # helper and setup functions below here

    def get_sockid_from_sessid(self, sessionid):
        return self.sio_sessionid_map.get(sessionid)

    def setup_logger(self, sock_session):
        sess_hash = sock_session['session_hash']
        sess_id = sock_session['session_id']
        sid = sock_session['socket_id']

        log.info("CONN LOGGER " + sess_hash)
        self.emit("logger_started", room=sid)

        overall_logger = logging.root
        formatter = overall_logger.handlers[0].formatter
        pattern = re.compile('^(?P<date>.*?)\s+'
                             '(?P<time>.*?)\s+'
                             '(?P<level>.*?)\s+'
                             '(?P<session_hash>.*?)\s+'
                             '(?P<name>.*?)\s+'
                             '(?P<message>.*?)$')

        overall_logger.info('{0} handlers attached'
                            .format(len(overall_logger.handlers)))
        # overall_logger.info('{0}'.format(self.socket))

        if len(overall_logger.handlers) > 50:
            # To stop the logger root from getting drowned in handlers
            del overall_logger.handlers[2]

        existing_handler = None

        for i, handler in enumerate(overall_logger.handlers):
            if (hasattr(handler, 'session_id') and
                    handler.session_id == sess_id):
                overall_logger.info('existing handler for the session '
                                    f'{sess_id} found')
                existing_handler = overall_logger.handlers[i]

        def gen_emit_msg(sess_hash):
            def emit_msg(logrecord):
                if (hasattr(logrecord, 'session_hash') and
                        logrecord.session_hash == sess_hash and
                        'server' not in logrecord.name):
                    msg_obj = (pattern.match(formatter.format(logrecord))
                               .groupdict())
                    del msg_obj['session_hash']
                    self.emit('log', msg_obj, sid)

                    return True
                else:
                    return False
            return emit_msg

        if existing_handler is None:
            session_filter = logging.Filter()
            session_filter.filter = gen_emit_msg(sess_hash)

            session_log_folder = os.path.join(os.getcwd(),
                                              'models', 'session', sess_id)

            if not os.path.exists(session_log_folder):
                pathlib.Path(session_log_folder).mkdir(parents=True,
                                                       exist_ok=True)

            session_log_file = os.path.join(session_log_folder,
                                            sess_id + '.log')
            session_handler = logging.handlers.RotatingFileHandler(
                session_log_file,
                mode='a',
                maxBytes=1000000,
                backupCount=3,
                encoding=None,
                delay=0
            )

            session_handler.formatter = formatter
            session_handler.session_id = sess_id
            overall_logger.info('handler for session {0} added'
                                .format(sess_id))
            session_handler.addFilter(session_filter)

            overall_logger.addHandler(session_handler)
        else:
            existing_handler.filters[0].filter = gen_emit_msg(sess_hash)


class GoodsFileNamespace(socketio.Namespace):
    '''
    Separate namespace for GOODS file requests
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sio_sessionid_map = {}
        self.active_requests = {}

    def get_sockid_from_sessid(self, sessionid):
        return self.sio_sessionid_map.get(sessionid)

    def on_connect(self, sid, environ):
        # get request context from the webgnome_api app
        # NOTE: next line will fail if server is restarted and an 'old'
        #       client tries to connect
        # Case for this situation needs to be added.
        # old environ contains old, invalid session_id, this is the problem
        # websocket connection is actually still successful?
        session_id = [s for s in environ['QUERY_STRING'].split('&')
                      if 'session_id' in s][0]
        session_id = session_id.split('=')[1]

        if session_id not in self.server.app.registry.settings['objects']:
            # connection has come in either before the session has been
            # properly established, or an old client socket is attempting to
            # reconnect to a new API
            self.disconnect(sid)
            return False

        sess_hash = generate_short_session_id(session_id)

        self.save_session(sid, {
            'session_id': session_id,
            'socket_id': sid,
            'session_hash': sess_hash,
            'request_id': None,
            'object': None,
        })

        return True

    def on_register(self, sid, request_id):
        '''
        When the client gets the list of request objects from the server,
        it must then communicate back with the socketio side per object
        to set up the connection the register function associates a
        (potentially new) session with the correct object
        '''
        with self.session(sid) as sock_session:
            sock_session['request_id'] = request_id
            obj = self.server.app.registry.settings['objects'][sock_session['session_id']][request_id]
            sock_session['object'] = obj

    def on_disconnect(self, sid):
        '''
        triggers automatically on webpage closure and refresh
        '''
        with self.session(sid) as sock_session:
            if not sock_session:
                return "session_not_found"

    def on_start_request(self, sid, request_id):
        with self.session(sid) as sock_session:
            req_obj = sock_session['object']
            req_obj.start_subset()
            self.emit('request_started', req_obj.start_time.isoformat(),
                      room=sid)

    def on_terminate_request(self, sid, request_id):
        request_object = self.get_request_object(sid, request_id)
        request_object.terminate_with_error('Client requested kill')
        # trigger kill on request object
        self.emit('terminated_request', request_id)

    def get_request_object(sid, request_id):
        with self.session(sid) as sock_session:
            return sock_session['objects'][request_id]
