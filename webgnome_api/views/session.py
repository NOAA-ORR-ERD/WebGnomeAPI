""" Cornice services.
"""
import logging

from cornice import Service
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
        log.info('session endpoint entered')
        log.info(f'session id before ensure: {session.session_id}')

        if isinstance(session.session_id, LazyCreateSession):
            log.info('session id is lazy; ensuring id now')
            session.ensure_id()
            log.info(f'session id after ensure: {session.session_id}')
            session['active_model'] = {}
            log.info('persisting new session')
            session.do_persist()
            log.info('session persisted')

        log.info('initializing in-memory session objects')
        init_session_objects(request, force=False)
        log.info('session endpoint returning id')

        return {'id': session.session_id}
    else:
        log.info(f'request has no session')
        return {'id': None}
