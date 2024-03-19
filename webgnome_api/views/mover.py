"""
Views for the Mover objects.
This currently includes ??? objects.
"""
import logging
import datetime as dt
import zlib
from threading import current_thread

import ujson

import numpy as np
from netCDF4 import Dataset, num2date, date2num

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound

from cornice import Service

from gnome.movers.c_current_movers import CurrentMoversBase
from gnome.movers import PyMover

from webgnome_api.common.views import (get_object,
                                       create_object,
                                       update_object,
                                       cors_policy,
                                       cors_response,
                                       cors_exception,
                                       switch_to_existing_session)

from webgnome_api.common.session_management import (get_session_object,
                                                    acquire_session_lock)

log = logging.getLogger(__name__)


edited_cors_policy = cors_policy.copy()
edited_cors_policy['headers'] = edited_cors_policy['headers'] + ('shape',)

mover = Service(name='mover', path='/mover*obj_id', description="Mover API",
                cors_policy=edited_cors_policy)

implemented_types = ('gnome.movers.simple_mover.SimpleMover',
                     'gnome.movers.c_wind_movers.PointWindMover',
                     'gnome.movers.random_movers.RandomMover',
                     'gnome.movers.random_movers.IceAwareRandomMover',
                     'gnome.movers.random_movers.RandomMover3D',
                     'gnome.movers.c_current_movers.CatsMover',
                     'gnome.movers.c_current_movers.ComponentMover',
                     'gnome.movers.c_current_movers.CurrentCycleMover',
                     'gnome.movers.py_current_movers.CurrentMover',
                     'gnome.movers.py_wind_movers.WindMover',
                     'gnome.movers.c_current_movers.c_GridCurrentMover',
                     'gnome.movers.c_current_movers.IceMover',
                     'gnome.movers.vertical_movers.RiseVelocityMover',
                     )


@mover.get()
def get_mover(request):
    content_requested = request.matchdict.get('obj_id')

    route = content_requested[1] if len(content_requested) > 1 else None

    if (route == 'grid'):
        return get_current_info(request)
    elif (route == 'centers'):
        return get_grid_centers(request)
    elif (route == 'vectors'):
        return get_vector_data(request)
    else:
        return get_object(request, implemented_types)


@mover.post()
def create_mover(request):
    '''Creates a Mover object.'''
    log.info(request.session.session_id)
    return create_object(request, implemented_types)


@mover.put()
def update_mover(request):
    '''Updates a Mover object.'''
    return update_object(request, implemented_types)


@view_config(route_name='mover_upload', request_method='OPTIONS')
def mover_upload_options(request):
    return cors_response(request, request.response)


@view_config(route_name='mover_upload', request_method='POST')
def upload_mover(request):
    switch_to_existing_session(request)
    log_prefix = 'req({0}): upload_mover():'.format(id(request))
    log.info('>>{}'.format(log_prefix))

    file_list = request.POST['file_list']
    file_list = ujson.loads(file_list)
    name = request.POST['name']
    file_name = file_list

    # This enables a time shift for gridded movers.
    # This isn't super awesome here, b/c this route is also used for loading
    # point winds. In that case the client just passes in a 0 value for tshift.
    # More robust support at the environment level in pyGNOME would be better.

    tshift = int(request.POST['tshift'])
    if tshift != 0:
        if isinstance(file_name, str):
            shift_time(file_name, tshift)
        else:
            for f in file_list:
                shift_time(f, tshift)

    log.info('  {} file_name: {}, name: {}'
             .format(log_prefix, file_name, name))

    mover_type = request.POST.get('obj_type', [])

    basic_json = {'obj_type': mover_type,
                  'filename': file_name,
                  'name': name}

    env_obj_base_json = {'obj_type': 'temp',
                         'name': name,
                         'data_file': file_name,
                         'grid_file': file_name,
                         'grid': {'obj_type': ('gnome.environment.'
                                               'gridded_objects_base.PyGrid'),
                                  'filename': file_name}
                         }

    wind_json = {'obj_type': 'gnome.environment.wind.Wind',
                 'filename': file_name,
                 'name': name,
                 'units': 'knots'}

    if ('py_wind_movers.WindMover' in mover_type):
        env_obj_base_json['obj_type'] = ('gnome.environment'
                                         '.environment_objects.GridWind')
        basic_json['wind'] = env_obj_base_json

    if ('py_current_movers.CurrentMover' in mover_type):
        env_obj_base_json['obj_type'] = ('gnome.environment'
                                         '.environment_objects.GridCurrent')
        basic_json['current'] = env_obj_base_json

    if ('c_wind_movers.PointWindMover' in mover_type):
        basic_json['wind'] = wind_json

    request.body = ujson.dumps(basic_json).encode('utf-8')

    mover_obj = create_mover(request)
    resp = Response(ujson.dumps(mover_obj))

    log.info('<<{}'.format(log_prefix))
    return cors_response(request, resp)


def shift_time(filename, tshift):
    '''
    Shift time by hours in tshift
    for reference:
          [[0,'GMT'],
          [-10,'HST (-10)'],
          [-9,'AKST (-9)'],
          [-8,'AKDT (-8)'],
          [-8,'PST (-8)'],
          [-7,'PDT (-7)'],
          [-7,'MST (-7)'],
          [-6,'MDT (-6)'],
          [-6,'CST (-6)'],
          [-5,'CDT (-5)'],
          [-5,'EST (-5)'],
          [-4,'EDT (-4)'],
          [-3,'ADT (-3)']]
    '''
    nc = Dataset(filename, 'r+')
    ncvars = nc.variables
    tvar = None

    try:
        ncvars['time']
        tvar = 'time'
    except KeyError:
        for var in ncvars:
            try:
                if ncvars[var].standard_name == 'time':
                    tvar = var
            except AttributeError:
                pass
    if tvar is not None:
        t = ncvars[tvar]
        offset = dt.timedelta(hours=tshift)
        oldtime = num2date(t[:], t.units)
        newtime = date2num(oldtime + offset, t.units)
        t[:] = newtime
        nc.close()


def get_current_info(request):
    '''
        Outputs GNOME current information for a particular current mover
        in a geojson format.
        The output is a collection of Features.
        The Features contain a MultiPolygon
    '''
    log_prefix = 'req({0}): get_current_info():'.format(id(request))
    log.info('>>' + log_prefix)

    session_lock = acquire_session_lock(request)
    log.info('  {} session lock acquired (sess:{}, thr_id: {})'
             .format(log_prefix, id(session_lock), current_thread().ident))
    try:
        obj_id = request.matchdict.get('obj_id')[0]
        mover = get_session_object(obj_id, request)

        if (mover is not None and
                isinstance(mover, (CurrentMoversBase, PyMover))):
            cells = get_cells(mover)

            return cells.reshape(-1, cells.shape[-1]*cells.shape[-2]).tolist()
        else:
            exc = cors_exception(request, HTTPNotFound)
            raise exc
    finally:
        session_lock.release()
        log.info('  {} session lock released (sess:{}, thr_id: {})'
                 .format(log_prefix, id(session_lock), current_thread().ident))

    log.info('<<' + log_prefix)


def get_grid_centers(request):
    '''
        Outputs GNOME grid centers for a particular mover
    '''
    log_prefix = 'req({0}): get_grid_centers():'.format(id(request))
    log.info('>>' + log_prefix)

    session_lock = acquire_session_lock(request)
    log.info('  {} session lock acquired (sess:{}, thr_id: {})'
             .format(log_prefix, id(session_lock), current_thread().ident))
    try:
        obj_id = request.matchdict.get('obj_id')[0]
        mover = get_session_object(obj_id, request)

        if (mover is not None and
                isinstance(mover, (CurrentMoversBase))):
            centers = get_center_points(mover)

            return centers.tolist()
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

        if obj is not None:
            log.info('{} found mover of type: {}'
                     .format(log_prefix, obj.__class__))
            vec_data = get_velocities(obj)

            resp = Response(
                content_type='arraybuffer',
                content_encoding='deflate'
            )

            resp.body, dshape = (zlib.compress(vec_data.tobytes()),
                                 vec_data.shape)

            resp.headers.add('Access-Control-Expose-Headers', 'shape')
            resp.headers.add('shape', str(dshape))

            return resp
        else:
            exc = cors_exception(request, HTTPNotFound)
            raise exc
    finally:
        session_lock.release()
        log.info('  {} session lock released (sess:{}, thr_id: {})'
                 .format(log_prefix, id(session_lock), current_thread().ident))

    log.info('<<' + log_prefix)


def get_grid_signature(mover):
    '''
        Here we are trying to get an n-dimensional signature of our
        grid data.
        There may be a better way to do this, but for now we will get the
        euclidian distances between all sequential points and sum them.
    '''
    points = mover.get_points()

    dtype = points[0].dtype.descr
    raw_points = points.view(dtype='<f8').reshape(-1, len(dtype))
    point_diffs = raw_points[1:] - raw_points[:-1]

    return abs(point_diffs.view(dtype=np.complex)).sum()


def get_cells(mover):
    if isinstance(mover, PyMover):
        raise TypeError('get_cells not supported on PyMover objects')
    grid_data = mover.get_grid_data()

    if not isinstance(mover, PyMover):
        d_t = grid_data.dtype.descr
        u_t = d_t[0][1]
        n_s = grid_data.shape + (len(d_t),)
        grid_data = grid_data.view(dtype=u_t).reshape(*n_s)

    return grid_data
    # return [t for t in grid_data.tolist()]


def get_center_points(mover):
    if hasattr(mover, 'mover'):
        return mover.mover._get_center_points()
    else:
        return mover.get_center_points()


def get_velocities(mover):
    return mover.mover._get_velocity_handle()


def get_tide_values(mover, times):
    return mover._tide.cy_obj.get_time_value(times)
