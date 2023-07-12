""" Cornice services.
"""
from cornice import Service
from pyramid_session_redis.util import LazyCreateSession

from webgnome_api.common.views import cors_policy
from webgnome_api.common.session_management import init_session_objects


session = Service(name='session', path='/session',
                  description="Session management", cors_policy=cors_policy)


@session.post()
def get_info(request):
    if hasattr(request, 'session'):
        session = request.session

        session.redis.config_set("notify-keyspace-events", "Ex")

        if isinstance(session.session_id, LazyCreateSession):
            session.ensure_id()
            session['active_model'] = {}
            session.do_persist()

        init_session_objects(request, force=False)

        return {'id': session.session_id}
    else:
        return {'id': None}
