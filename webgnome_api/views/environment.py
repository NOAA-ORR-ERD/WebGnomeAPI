"""
Views for the Environment objects.
This currently includes Wind and Tide objects.
"""
import ujson
import logging
import zlib
import numpy as np
from threading import current_thread

from pyramid.settings import asbool
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPNotImplemented

from cornice import Service

from gnome.environment.environment_objects import GridCurrent, GridWind

from webgnome_api.common.views import (get_object,
                                       create_object,
                                       update_object,
                                       cors_policy,
                                       cors_response,
                                       cors_exception,
                                       process_upload,
                                       can_persist,
                                       switch_to_existing_session,
                                       activate_uploaded)

from webgnome_api.common.session_management import (get_session_object,
                                                    acquire_session_lock)

log = logging.getLogger(__name__)

edited_cors_policy = cors_policy.copy()
edited_cors_policy['headers'] = edited_cors_policy['headers'] + ('shape',)

env = Service(name='environment', path='/environment*obj_id',
              description="Environment API",
              cors_policy=edited_cors_policy,
              # accept='application/json+octet-stream',
              content_type=['application/json', 'binary'])

implemented_types = ('gnome.environment.Tide',
                     'gnome.environment.Wind',
                     'gnome.environment.Water',
                     'gnome.environment.Waves',
                     'gnome.environment.environment_objects.GridCurrent',
                     'gnome.environment.environment_objects.GridWind',
                     )


@env.get()
def get_environment(request):
    '''Returns an Gnome Environment object in JSON.'''
    content_requested = request.matchdict.get('obj_id')

    resp = Response(
        content_type='arraybuffer',
        content_encoding='deflate'
    )

    if (len(content_requested) > 1):
        route = content_requested[1] if len(content_requested) > 1 else None

        if route == 'grid':
            resp.body = get_grid(request)
            return cors_response(request, resp)
        if route == 'vectors':
            resp.body, dshape = get_vector_data(request)
            resp.headers.add('Access-Control-Expose-Headers', 'shape')
            resp.headers.add('shape', str(dshape))
            return cors_response(request, resp)
        if route == 'nodes':
            resp.body = get_nodes(request)
            return cors_response(request, resp)
        if route == 'centers':
            resp.body = get_centers(request)
            return cors_response(request, resp)
        if route == 'metadata':
            return get_metadata(request)
    else:
        return get_object(request, implemented_types)


@env.post()
def create_environment(request):
    '''Creates an Environment object.'''
    return create_object(request, implemented_types)


@env.put()
def update_environment(request):
    '''Updates an Environment object.'''
    return update_object(request, implemented_types)


@view_config(route_name='environment_upload', request_method='OPTIONS')
def environment_upload_options(request):
    return cors_response(request, request.response)


@view_config(route_name='environment_upload', request_method='POST')
def upload_environment(request):
    switch_to_existing_session(request)
    log_prefix = 'req({0}): upload_environment():'.format(id(request))
    log.info('>>{}'.format(log_prefix))

    file_list = request.POST['file_list']
    file_list = ujson.loads(file_list)
    name = request.POST['name']
    file_name = file_list[0]

    log.info('  {} file_name: {}, name: {}'
             .format(log_prefix, file_name, name))

    env_type = request.POST.get('obj_type', [])
    request.body = ujson.dumps({'obj_type': env_type,
                                'filename': file_name,
                                'name': name
                                }).encode('utf-8')

    env_obj = create_environment(request)
    resp = Response(ujson.dumps(env_obj))

    log.info('<<{}'.format(log_prefix))
    return cors_response(request, resp)


@view_config(route_name='environment_activate', request_method='OPTIONS')
def activate_environment_options(request):
    return cors_response(request, request.response)


@view_config(route_name='environment_activate', request_method='POST')
@can_persist
def activate_environment(request):
    '''
        Activate an environment file that has already been persistently
        uploaded.
    '''
    log_prefix = 'req({0}): activate_environment():'.format(id(request))
    log.info('>>{}'.format(log_prefix))

    file_name, name = activate_uploaded(request)
    resp = Response(ujson.dumps({'filename': file_name, 'name': name}))

    log.info('<<{}'.format(log_prefix))
    return cors_response(request, resp)


def get_grid(request):
    '''
        Outputs the object's grid cells in binary format
    '''
    log_prefix = 'req({0}): get_grid():'.format(id(request))
    log.info('>>' + log_prefix)

    session_lock = acquire_session_lock(request)
    log.info('  {} session lock acquired (sess:{}, thr_id: {})'
             .format(log_prefix, id(session_lock), current_thread().ident))
    try:
        obj_id = request.matchdict.get('obj_id')[0]
        obj = get_session_object(obj_id, request)

        if obj is not None and isinstance(obj, (GridCurrent, GridWind)):
            cells = obj.grid.get_cells()

            return zlib.compress(cells.astype(np.float32).tobytes())
        else:
            exc = cors_exception(request, HTTPNotFound)
            raise exc
    finally:
        session_lock.release()
        log.info('  {} session lock released (sess:{}, thr_id: {})'
                 .format(log_prefix, id(session_lock), current_thread().ident))

    log.info('<<' + log_prefix)


def get_vector_data(request):
    log_prefix = 'req({0}): get_grid():'.format(id(request))
    log.info('>>' + log_prefix)

    session_lock = acquire_session_lock(request)
    log.info('  {} session lock acquired (sess:{}, thr_id: {})'
             .format(log_prefix, id(session_lock), current_thread().ident))
    try:
        obj_id = request.matchdict.get('obj_id')[0]
        obj = get_session_object(obj_id, request)

        if obj is not None and isinstance(obj, (GridCurrent, GridWind)):
            vec_data = obj.get_data_vectors()

            return zlib.compress(vec_data.tobytes()), vec_data.shape
        else:
            exc = cors_exception(request, HTTPNotFound)
            raise exc
    finally:
        session_lock.release()
        log.info('  {} session lock released (sess:{}, thr_id: {})'
                 .format(log_prefix, id(session_lock), current_thread().ident))

    log.info('<<' + log_prefix)


def get_metadata(request):
    log_prefix = 'req({0}): get_current_info():'.format(id(request))
    log.info('>>' + log_prefix)

    session_lock = acquire_session_lock(request)
    log.info('  {} session lock acquired (sess:{}, thr_id: {})'
             .format(log_prefix, id(session_lock), current_thread().ident))
    try:
        obj_id = request.matchdict.get('obj_id')[0]
        obj = get_session_object(obj_id, request)
        if obj is not None:
            return obj.get_metadata()
        else:
            exc = cors_exception(request, HTTPNotFound)
            raise exc
    finally:
        session_lock.release()
        log.info('  {} session lock released (sess:{}, thr_id: {})'
                 .format(log_prefix, id(session_lock), current_thread().ident))

    log.info('<<' + log_prefix)


def get_grid_signature(obj):
    '''
        Here we are trying to get an n-dimensional signature of our
        grid data.
        There may be a better way to do this, but for now we will get the
        euclidian distances between all sequential points and sum them.
    '''
    points = obj.get_points()

    dtype = points[0].dtype.descr
    raw_points = points.view(dtype='<f8').reshape(-1, len(dtype))
    point_diffs = raw_points[1:] - raw_points[:-1]

    return abs(point_diffs.view(dtype=np.complex)).sum()
