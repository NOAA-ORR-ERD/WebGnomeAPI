"""
Common Gnome object request handlers.
"""
import logging
from threading import Lock
from pathlib import Path

from pyramid_session_redis.util import LazyCreateSession
from pyramid.httpexceptions import HTTPException

log = logging.getLogger(__name__)


def req_session_is_valid(funct):
    '''
        This is a decorator function intended to short-circuit a view by
        returning None if the session in the request is not valid.
    '''
    def helper(request, **kwargs):
        if isinstance(request.session.session_id, LazyCreateSession):
            return None
        else:
            return funct(request, **kwargs)

    return helper


def exception_if_none(funct, exc_type=HTTPException):
    '''
        This is a decorator function intended to raise an exception if the
        result of a view-styled function returns None.  View-styled means that
        a WSGI request object is passed in.
    '''
    def helper(request):
        ret = funct(request)
        if ret is None:
            raise exc_type
        else:
            return ret

    return helper


def init_session_objects(request, force=False):
    session = request.session
    obj_pool = request.registry.settings['objects']

    if (session.session_id not in obj_pool) or force:
        obj_pool[session.session_id] = {}

    objects = obj_pool[session.session_id]

    if 'gnome_session_lock' not in objects:
        objects['gnome_session_lock'] = Lock()


@req_session_is_valid
def get_session_objects(request):
    init_session_objects(request)
    obj_pool = request.registry.settings['objects']

    return obj_pool[request.session.session_id]


def get_session_object(obj_id, request):
    objects = get_session_objects(request)

    return None if objects is None else objects.get(obj_id, None)


def set_session_object(obj, request, obj_id=None):
    objects = get_session_objects(request)

    if obj_id is not None:
        objects[obj_id] = obj
    else:
        try:
            objects[obj.id] = obj
        except AttributeError:
            objects[id(obj)] = obj


def acquire_session_lock(request):
    session_lock = get_session_object('gnome_session_lock', request)
    session_lock.acquire()

    return session_lock


def set_active_model(request, obj_id):
    session = request.session

    if not ('active_model' in session and
            session['active_model'] == obj_id):
        session['active_model'] = obj_id
        session.do_persist()


def get_active_model(request):
    session = request.session

    if 'active_model' in session and session['active_model']:
        return get_session_object(session['active_model'], request)
    else:
        return None


@req_session_is_valid
def get_uncertain_models(request):
    session_id = request.session.session_id
    uncertainty_models = request.registry.settings['uncertain_models']

    if session_id in uncertainty_models:
        return uncertainty_models[session_id]
    else:
        return None


@req_session_is_valid
def set_uncertain_models(request):
    from gnome.multi_model_broadcast import ModelBroadcaster

    session_id = request.session.session_id
    uncertain_models = request.registry.settings['uncertain_models']

    active_model = get_active_model(request)
    if active_model:
        model_broadcaster = ModelBroadcaster(active_model,
                                             ('down', 'normal', 'up'),
                                             ('down', 'normal', 'up'),
                                             'ipc_files')

        uncertain_models[session_id] = model_broadcaster


@req_session_is_valid
def drop_uncertain_models(request):
    session_id = request.session.session_id
    uncertain_models = request.registry.settings['uncertain_models']

    if (session_id in uncertain_models and
            uncertain_models[session_id] is not None):
        uncertain_models[session_id].stop()
        uncertain_models[session_id] = None


def register_exportable_file(request, basename, filepath):
    session = request.session

    if 'registered_files' not in session:
        session['registered_files'] = {}

    file_reg = session['registered_files']
    if basename in file_reg:
        if filepath != file_reg[basename]:
            log.warning('Overwriting registered file: {0}'.format(basename))
            log.warning('Old Filepath: {0}'.format(file_reg[basename]))
            log.warning('New Filepath: {0}'.format(filepath))
    file_reg[basename] = filepath

    session['registered_files'] = file_reg
    session.do_persist()


def clear_exportable_files(request):
    session = request.session
    session['registered_files'] = {}
    session.do_persist()


def unregister_exportable_file(request, basename):
    # if for some reason we need to do this...
    session = request.session
    if ('registered_files' in session and
            basename in session['registered_files']):
        del session['registered_files'][basename]
        session.do_persist()

def search_registered_file(request, basename, obj_id=None):
    # If an obj_id is provided, if the object is registered in the session
    # then we can search for possible filenames in the object schema
    if obj_id is not None:
        obj = get_session_object(obj_id, request)
        if obj is not None:
            potential_fn_attrs = obj._schema().get_nodes_by_attr('isdatafile')
            for fn_attr in potential_fn_attrs:
                fn = Path(getattr(obj, fn_attr))
                if fn.exists() and fn.is_file() and fn.name == basename:
                    register_exportable_file(request, basename, str(fn))
                    return str(fn)
        else:
            return None
    else:
        return get_registered_file(request, basename)

def get_registered_file(request, basename):
    return request.session.get('registered_files', {}).get(basename, None)
