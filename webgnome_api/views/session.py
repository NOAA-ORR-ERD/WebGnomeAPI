""" Cornice services.
"""
import logging

from cornice import Service
from gevent import Timeout
from pyramid.httpexceptions import HTTPGatewayTimeout
from pyramid_session_redis.util import LazyCreateSession

from webgnome_api.common.views import cors_policy
from webgnome_api.common.session_management import init_session_objects

log = logging.getLogger(__name__)

session = Service(name='session', path='/session',
                  description="Session management", cors_policy=cors_policy)


@session.post()
def get_info(request):
    if hasattr(request, 'session'):
        session = request.session
        redis_op_timeout = float(request.registry.settings.get(
            'redis.sessions.request_timeout', 5
        ))
        # log.info('session endpoint entered')
        # log.info(f'session id before ensure: {session.session_id}')

        if isinstance(session.session_id, LazyCreateSession):
            # log.info('session id is lazy; ensuring id now')
            with Timeout(redis_op_timeout, False):
                session.ensure_id()
            if isinstance(session.session_id, LazyCreateSession):
                raise HTTPGatewayTimeout(
                    f'Session ensure_id timed out after {redis_op_timeout}s'
                )
            # log.info(f'session id after ensure: {session.session_id}')
            session['active_model'] = {}
            # log.info('persisting new session')
            with Timeout(redis_op_timeout, False):
                session.do_persist()
            # log.info('session persisted')

        # log.info('initializing in-memory session objects')
        init_session_objects(request, force=False)
        # log.info('session endpoint returning id')

        return {'id': session.session_id}
    else:
        log.info(f'request has no session')
        return {'id': None}
