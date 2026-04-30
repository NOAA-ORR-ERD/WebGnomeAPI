"""
Views for the GOODS interface.
"""
import os
import time
import datetime
import logging
import threading
import multiprocessing
from multiprocessing import Process
import queue
from uuid import uuid1

import ujson

from cornice import Service

from pyramid.httpexceptions import (HTTPInsufficientStorage,
                                    HTTPBadRequest,
                                    HTTPNotFound)

from webgnome_api.common.system_resources import get_free_space
from webgnome_api.common.common_object import get_session_dir
from webgnome_api.common.session_management import (get_session_objects,
                                                    register_exportable_file)
from webgnome_api.common.views import (cors_policy,
                                       cors_response,
                                       HTTPPythonError,
                                       gen_unique_filename)

from webgnome_api import supported_ocean_models, supported_met_models

try:
    from libgoods import api, FileTooBigError
    import libgoods
except ImportError:
    print("libgoods package not available "
          "-- its functionality will not be there")

from dask.callbacks import Callback
from timeit import default_timer


log = logging.getLogger(__name__)

goods_maps = Service(name='maps', path='/goods/maps*',
                     description="GOODS MAP API", cors_policy=cors_policy)

goods_nws_wind = Service(name='nws', path='/goods/nws*',
                         description="GOODS NWS Point Wind API",
                         cors_policy=cors_policy)

goods_validation = Service(name='validation', path='/goods/validation*',
                           description="GOODS SUBSET VALIDATION API",
                           cors_policy=cors_policy)

goods_list_models = Service(name='list_models', path='/goods/list_models*',
                            description="GOODS METADATA API",
                            cors_policy=cors_policy)

goods_requests = Service(name='goods_requests', path='/goods_requests*',
                         description="GOODS REQUESTS API",
                         cors_policy=cors_policy)


@goods_list_models.get()
def get_model_metadata(request):
    '''
    gets a list set of the metadata objects for all available models.

    parameters:

    `map_bounds`:

    If map_bounds is set, only models that intersect those
    bounds will be returned.

    map_bounds is a polygon as a list of lon, lat pairs

    `request_type`: what type of data you are looking for. A list of:

    'surface currents'
    '3D currents'
    'surface winds'

    But only: ["surface_currents"] is tested
    '''
    model_id = request.GET.get('model_id', None)

    bounds = request.GET.get('map_bounds', None)
    if bounds:
        bounds = ujson.loads(bounds)


    request_type = request.GET.get('request_type')
    if request_type:
        request_type = ujson.loads(request_type)

    try:
        if any(cur in request_type for cur in ('surface currents',
                                               '3D currents')):
            supported_env_models = supported_ocean_models
        elif 'surface winds' in request_type:
            supported_env_models = supported_met_models
        else:
            supported_env_models = {}
    except TypeError:
        supported_env_models = [supported_ocean_models + supported_met_models]
    retval = None

    if model_id:
        # AM comment: I don't think this every executes
        # (for specific model its parsed from metadata list)
        # CHB: ran webgnome dev, and this is used.
        mdl = api.get_model(model_id)
        retval =  mdl.metadata.as_pyson()
    else:
        retval = api.list_models(
            model_ids=supported_env_models,
            map_bounds=bounds,
            env_params=request_type,
            )

    return retval


@goods_validation.get()
def validate_subset(request):
    '''

    subset_bounds is a polygon as a list of lon, lat pairs
    '''
    params = request.GET
    w = float(params['WestLon'])
    s = float(params['SouthLat'])
    e = float(params['EastLon'])
    n = float(params['NorthLat'])

    subset_bounds = ((w, s), (w, n), (e, n), (e, s))
    start = request.GET.get('start_time', None)
    end = request.GET.get('end_time', None)
    model_id = request.GET.get('model_id', None)
    try:
        retval = api.validate_subset(
            model_id,
            start,
            end,
            subset_bounds,
            )
    except Exception as e:
        return cors_response(request, HTTPPythonError(e))

    return retval


@goods_maps.post()
def get_goods_map(request):
    '''
    Uses the payload passed by the client to make a .bna download request
    from GOODS.
    This file is then used to create a map object, which is then returned
    to the client

    Example post:
    req_params = {'err_placeholder':'',
                  'NorthLat': 47.06693175688763,
                  'WestLon': -124.26942110656861,
                  'EastLon': -123.6972360021842,
                  'SouthLat': 46.78488364986247,
                  'xDateline': 0,
                  'resolution': 'i',
                  'submit': 'Get Map',
                  }
    '''

    params = request.POST

    max_upload_size = eval(request.registry.settings['max_upload_size'])

    w = float(params['WestLon'])
    s = float(params['SouthLat'])
    e = float(params['EastLon'])
    n = float(params['NorthLat'])

    subset_bounds = ((w, s), (w, n), (e, n), (e, s))

    try:
        fn, contents = api.get_map(
            bounds=subset_bounds,
            resolution=params['resolution'],
            data_source=params['shoreline'],
            cross_dateline=bool(int(params['xDateline'])),
            max_filesize=max_upload_size,
        )

    except FileTooBigError:
        raise cors_response(request,
                            HTTPBadRequest('file is too big!  Max size = {}'
                                           .format(max_upload_size)))

    size = len(contents)

    upload_dir = os.path.relpath(get_session_dir(request))

    if size >= get_free_space(upload_dir):
        raise cors_response(request,
                            HTTPInsufficientStorage('Not enough space '
                                                    'to save the file'))

    file_name, unique_name = gen_unique_filename(fn, upload_dir)

    file_path = os.path.join(upload_dir, unique_name)

    log.info('Registering filename ' + file_path)
    register_exportable_file(request, file_name, file_path)

    with open(file_path, 'w') as fp:
        fp.write(contents)

    log.info('Successfully uploaded file "{0}"'.format(file_path))

    return file_path, file_name


@goods_nws_wind.get()
def get_nws_wind(request):
    '''
    Uses the payload passed by the client to make a NWS wind request
    from libGOODS.
    This file is then used to create a map object, which is then returned
    to the client

    Example post:
    req_params = {
                  'latitude': '47.06693175688763',
                  'longitude': '-124.26942110656861',
                  }
    '''
    params = request.GET
    try:
        data = api.NWS_point_wind(lon=params['longitude'],
                                  lat=params['latitude'])
    except ValueError as e:
        return cors_response(request, HTTPNotFound(e))

    return data


def create_goods_request(request):
    '''
    Uses the payload passed by the client to send information to
    libGOODS. This file returned from libgoods is then used to create a
    CurrentMover object, which is then returned to the client

    class FetchConfig:
        """Configuration data class for fetching."""

        model_id: str
        output_pth: Path
        start: pd.Timestamp
        end: pd.Timestamp
        bbox: Tuple[float, float, float, float]
        source: str
        standard_names: List[str] = field(default_factory=lambda: STANDARD_NAMES)
    '''

    log_prefix = 'req{0}: get_currents()'.format(id(request))
    log.info('>>' + log_prefix)

    params = request.POST
    upload_dir = os.path.relpath(get_session_dir(request))
    _max_upload_size = eval(request.registry.settings['max_upload_size'])

    w = float(params['WestLon'])
    s = float(params['SouthLat'])
    e = float(params['EastLon'])
    n = float(params['NorthLat'])

    subset_bounds = ((w, s), (w, n), (e, n), (e, s))

    cross_dateline = bool(int(params['cross_dateline']))
    request_type = params['request_type']
    tshift = 0  # eliminating this but not done entirely yet (mover.py)

    include_winds = params.get('include_winds', True) not in ('false',
                                                              'False',
                                                              None)
    if include_winds:
        request_type = [request_type, 'surface winds']

    # generate a unique model output name
    start = params['start_time']
    end = params['end_time']

    fname = '{}_{}_{}.nc'.format(params['model_id'],
                                 start.split("T")[0],
                                 end.split("T")[0])

    _file_name, unique_name = gen_unique_filename(fname, upload_dir)
    output_path = os.path.join(upload_dir, unique_name)

    session_objs = get_session_objects(request)
    request_id = str(uuid1())
    goods_req = GOODSRequest(
        start_time=datetime.datetime.now(),
        orig_request=request,
        request_id=request_id,
        filename=unique_name,
        outpath=output_path,
        request_type=request_type,
        request_args={
            'model_id': params['model_id'],
            'start': start,
            'end': end,
            'bounds': subset_bounds,
            'cross_dateline': cross_dateline,
            'environmental_parameters': request_type,
            'libgoods_archive': libgoods.config.archive_dir,
        },
        tshift=tshift,
        _debug=False
    )

    session_objs[request_id] = goods_req
    goods_req.start()

    return goods_req


@goods_requests.post()
def goods_request(request):
    '''
    This route is used to create, cancel or reconfirm requests
    returns the updated request object

    Example Query (subset of GFS winds)

    command create
    model_id GFS
    NorthLat 32.13693712654453
    WestLon -150.47064739438775
    EastLon -105.48316958086902
    SouthLat 11.331783933709263
    start_time 2026-03-18T16:00:00
    end_time 2026-03-20T16:00:00
    surface_only true
    cross_dateline 0
    include_winds false
    request_type surface winds

    '''

    log_prefix = 'req{0}: interact_request() {1}'.format(
        id(request),
        request.POST.get('command', 'NO COMMAND')
    )
    log.info('>>' + log_prefix)

    params = request.POST
    command = params.get('command', 'None')

    req_id = session_objs = req_obj = None
    if command != 'create':
        req_id = params.get('request_id', None)
        session_objs = get_session_objects(request)
        req_obj = session_objs.get(req_id, None)

    if command == 'create':
        new_req = create_goods_request(request)
        return new_req.to_response()

    elif command == 'cancel':
        req_obj.cancel_request()
        return req_obj.to_response()

    elif command == 'retry':
        req_obj.retry_request()
        return req_obj.to_response()

    elif command == 'reconfirm':
        req_obj.reconfirm()
        return req_obj.to_response()

    elif command == '_debugPause':
        req_obj._debugPause()
        return req_obj.to_response()

    elif command == 'outpath':
        if req_obj.state != 'finished':
            raise ValueError(f'Request {req_obj.request_id} is not finished')
        else:
            return req_obj.outpath

    elif command == 'cleanup':
        # if for some reason the client wants to wipe one or all requests
        if req_id == 'all':
            for obj in session_objs.values():
                if isinstance(obj, GOODSRequest):
                    log.info(f'Batch-remove GOODS request {obj.request_id}')
                    session_objs[obj.request_id].dead()
                    del session_objs[obj.request_id]
        else:
            obj = session_objs.get(req_id, None)
            if not obj:
                return
            log.info('Removing GOODS request {0}'.format(obj.request_id))
            del session_objs[obj.request_id]

    else:
        raise ValueError(f'Unrecognized command ({command}) '
                         'to goods_request interface')


@goods_requests.get()
def get_goods_requests(request):
    '''
    If the client needs to request all currently open GOODS requests,
    this is the function that handles it.

    returns to the client a jsonified list of GOODSRequest objects
    '''
    # log_prefix = 'req{0}: get_currents()'.format(id(request))
    # log.info('>>' + log_prefix)
    session_objs = get_session_objects(request)

    params = request.GET
    if params.get('id', None) and params['id'] in session_objs:
        # if GET is provided a single request_id,
        # it will return only that request
        return session_objs['request_id'].to_response()

    all_requests = [v for _k, v in session_objs.items()
                    if isinstance(v, GOODSRequest)]
    open_requests = [r for r in all_requests if r.state != 'dead']

    typ = request.GET.get('request_type', None)
    rv = None
    if typ:
        rv = [r.to_response() for r in open_requests if typ in r.request_type]
    else:
        rv = [r.to_response() for r in open_requests]

    for _idx, r in enumerate(open_requests):
        if r.subset_process is not None:
            log.info('>>>>>'
                     f'Req {r.request_id} '
                     f'subset {r.subset_process.is_alive()}')
        else:
            log.info('>>>>>'
                     f'Req {r.request_id} '
                     f'No subset subprocess')

    return rv


class GOODSRequest(object):
    '''
    Manages a GOODS data subset operation and progress tracking

    This object is intended to be created inside a request handler and put into
    the session objects dict. This provides management and persistence.

    This object has 6 primary states: 'preparing', 'subsetting', 'requesting',
    'too_large', 'error', and 'dead'.
    It is initialized in the 'preparing' state, and goes to the
    'subsetting' state after calling the relevant method.
    '''
    logger = multiprocessing.log_to_stderr()

    def __init__(self,
                 request_id=None,
                 orig_request=None,
                 start_time=None,
                 request_type=None,
                 request_args=None,
                 filename=None,
                 outpath=None,
                 tshift=0,
                 _debug=False,
                 _reconfirm_timeout=60,  # seconds to wait for reconfirmation before marking request as failed
                 ):
        '''
        Object to represent an open asynchronous file retrieval.
        '''
        if start_time is None:
            start_time = datetime.datetime.now()
        self.start_time = start_time
        self.request_id = request_id
        self.orig_request = orig_request
        self.request_type = request_type  # 'currents' or 'winds'
        self.request_args = request_args
        self.subset_size = None
        self.filename = filename
        self.outpath = outpath
        self.tshift = tshift
        self.error_type = ''
        self.subset_time = 0
        self.retrieve_time = 0

        # timezone shift retained for future use by webgnomeapi
        # self.tshift = float(tshift) if tshift != 'NaN' else None

        self._debug = _debug
        self._max_size = int(self.orig_request.registry.settings.get('max_goods_request_size', 10000000000))
        self._reconfirm_timeout = _reconfirm_timeout
        self.logger = self.__class__.logger

        # Communication attributes (should be reset if request retried)
        self.message = None  # set by worker thread
        self.state = 'preparing'
        self.time_elapsed = 0

        # Process objects for subset and request operations
        self.subset_process = None
        self.request_process = None

        # lock for main thread to clear on reconfirmation
        self.pause_event = threading.Event()

        # event for main thread to set if cancellation desired
        self.cancel_event = threading.Event()

        # event for worker thread to set when request is complete
        self.complete_event = threading.Event()

    def to_response(self):
        return {'start_time': self.start_time.isoformat(),
                'request_id': self.request_id,  # GOODSRequest do not have an 'id' as a distinction from GnomeId
                'id': self.request_id,  # 'id' specifically needed by Backbone.Collection so merging works right
                'request_type': self.request_type,
                'filename': self.filename,
                'state': self.state,
                'size': self.subset_size,
                'time_elapsed': self.time_elapsed,
                'message': repr(self.message),
                'outpath': self.outpath,
                'tshift': self.tshift,
                'error_type': self.error_type,
                'subset_time': self.subset_time,
                'retrieve_time': self.retrieve_time,
                }

    @property
    def subset_xr(self):
        if not self._subset_finished:
            raise ValueError('Subset operation not completed')
        else:
            return self._subset_xr

    @subset_xr.setter
    def subset_xr(self, subs):
        if not self._subset_finished:
            raise ValueError('Subset operation not completed')
        else:
            self._subset_xr = subs

    def start(self):
        logger = self.logger
        logger.setLevel(multiprocessing.SUBDEBUG)
        if self.state != 'preparing':
            msg = (f'Subset operation {self.request_id} '
                   'already started or completed')
            self.write_log(msg, 'error', 'main')
            return msg
        self._subset_finished = False

        message_queue = multiprocessing.Queue()
        message_queue.write = message_queue.put

        logger.info(f'Starting GOODS request {self.request_id}')
        # if (not hasattr(libgoods.config, 'archive_dir') or
        #         self.orig_request.config.local_archive_dir is not None):
        #     raise EnvironmentError('libgoods archive directory not set '
        #                            '(main thread)')
        self.request_thread = threading.Thread(
            target=self._thread_request_func,
            args=(self.request_args, logger, message_queue),
            daemon=True
        )
        self.request_thread.start()

    def too_large(self):
        size = self._subset_xr.ds.nbytes
        self.state = 'too_large'
        self.message = (f'Subset size is very large ({size}). '
                        'Reconfirm required.')
        self.pause_event.clear()
        if not self.pause_event.wait(timeout=self._reconfirm_timeout):
            self.cancel_request()
            return

    def error(self, t, msg):
        self.state = 'error'
        self.error_type = t
        self.message = msg

    def reset(self):
        self.state = 'preparing'
        self.message = None
        self.error_type = ''
        self.time_elapsed = 0
        self._subset_finished = False
        self._request_finished = False
        self._subset_xr = None
        self._request_xr = None
        if self.subset_process:
            self.subset_process.terminate()
        if self.request_process:
            self.request_process.terminate()
        if self.request_thread:
            try:
                self.request_thread.join(timeout=5)
            except Exception as e:
                self.logger.error('Request thread join error: ' + repr(e))
                raise
            self.request_thread = None

    def reconfirm(self):
        if self.state == 'too_large':
            self.state = 'subsetting'
        self.pause_event.set()  # releases the waiting request thread

    def _debugPause(self):
        breakpoint()

    def cancel_request(self):
        'terminate any running processes or threads and mark request as dead'
        self.cancel_event.set()
        self.state = 'dead'
        if self.subset_process:
            self.subset_process.terminate()
        if self.request_process:
            self.request_process.terminate()
        if self.request_thread:
            try:
                self.request_thread.join(timeout=5)
            except Exception as e:
                self.logger.error('Request thread failed to join upon cancel_request: ' + repr(e))
                raise

    def retry_request(self):
        self.reset()
        self.start()

    def _thread_request_func(self, request_args, logger, mq):
        if (not hasattr(libgoods.config, 'archive_dir') and
                self.orig_request.config.local_archive_dir is not None):
            raise EnvironmentError('libgoods archive directory not set '
                                   '(worker thread)')
        logger.info('START')
        # STEP 1: Subset process to query libgoods for model subset
        status = result = None
        if (self.orig_request.registry.settings.get('goods_use_subprocess_subset', 'true') == 'true'):
            # use a subprocess
            # self.outpath so that the subprocess also writes the file
            #  - a bit of a hack, shold be rethought?
            self.subset_process = Process(target=subset_process_func,
                                          args=(request_args, mq, self.outpath),
                                          daemon=True)
            self.subset_process.start()
            try:
                status = mq.get(timeout=30)  # startup timeout (expected msg 'startup')
            except queue.Empty:
                msg = f'Subset process failed to start within timeout for request {self.filename}'
                logger.error(msg)
                self.error('startup_timeout', msg)
                return
            self.state = 'subsetting'
            msg = '0'
            counter = 0
            timeout = 180
            timevar = 'subset_time'
            #rudimentary progress loop to capture messages from the subset process and update time elapsed until process finishes or times out
            while counter < timeout:  # 3 minutes until loop times out
                logger.info('SUBSET PROGESS: ' + str(counter))
                try:
                    msg = mq.get(timeout=2)
                    if msg == 'success' or msg == 'error':
                        #next message is result or error message.
                        logger.info('leaving progress loop via break')
                        logger.info('Message: {0}'.format(msg))
                        logger.info('Joining subset process')
                        status = msg
                        try:
                            result = mq.get(timeout=30)
                        except queue.Empty:
                            m = f'Subset process reported success or error but failed to send final result through queue before timeout expired for request {self.filename}'
                            logger.error(m)
                            self.error('join_timeout', m)
                        break
                    elif msg == 'subset_complete':
                        logger.info('Subset process reported subset_complete')
                        self.state = 'retrieving'
                        self.message = 'Subset complete, retrieving data'
                        self._subset_finished = True
                        try:
                            result = mq.get(timeout=30)  # wait for result or error message
                        except queue.Empty:
                            m = f'Subset process reported subset_complete but failed to send final result through queue before timeout expired for request {self.filename}'
                            logger.error(m)
                            self.error('join_timeout', m)
                        self.subset_size = result
                        if self.subset_size > self._max_size:
                            self.too_large()
                        mq.put('proceed')
                    else:
                        if msg:
                            logger.info('Message: {0}'.format(msg))
                        self.time_elapsed = counter
                except queue.Empty:
                    counter += 2
                    if self.state == 'subsetting':
                        self.subset_time = counter
                    elif self.state == 'retrieving':
                        self.retrieve_time = counter - self.subset_time
                    elif self.state == 'preparing':
                        logger.info('Request has been retried. thread should be exiting. breaking loop.')
                        return
                    elif hasattr(self.subset_process, 'exitcode') and self.subset_process.exitcode is not None:
                        logger.info('Subset process has exited with exitcode ' + str(self.subset_process.exitcode) + '. Breaking progress loop.')
                        break
                    self.time_elapsed = counter
                    
            mq.close()
            mq.cancel_join_thread()
            self.subset_process.join(5) # give it a few seconds to clean up if it finished while we were waiting for messages
            if hasattr(self.subset_process, 'exitcode') and self.subset_process.exitcode is None and counter >= timeout:
                # process still running (self.subset_process.exitcode is None), and timeout exceeded
                m = f'Subset process exceeded timeout of {timeout} seconds for request {self.filename}'
                self.error('subset_timeout', m)
                return
            elif hasattr(self.subset_process, 'exitcode') and (self.subset_process.exitcode or status == 'error'):
                logger.info('SUBSET FAILED: '
                            f'exitcode: {self.subset_process.exitcode}')
                self.error('subprocess_error', 'Subset process reported error: ' + repr(result))
                return
        else: # not using a subprocess for the subsetting, etc.
            # this is barely tested, definitely not safe for production...
            # might be better to call subset_process_func() (with dummpy mq)
            # that that the code stays in sync.
            request_args.pop('libgoods_archive', None)
            result = api.get_model_subset(**request_args)
            result.write_nc(outpath)
            status = 'success'
        logger.info('RESULT: {}'.format(repr(result)))
        # Needs further development in the client before we can add this back in.

        self._request_finished = True
        self.state = 'finished'
        self.percent = 100
        register_exportable_file(self.orig_request, self.filename, self.outpath)
        self.complete_event.set()
        # logger.close()


class Tracker(Callback):
    def __init__(self, model, dt=1, timeout=60):
        self.dt = 1
        self.timeout = timeout
        self.model = model
        self.timer_greenlet = None

    def _start(self, dsk):
        self.state = None
        self.start_time = default_timer()
        self.running = True
        self.timer_thread = threading.Thread(
            target=self._timer_func,
            name='TimerThread' + self.model.request_id,
            daemon=True,
            )
        self.timer_thread.start()

    def _pretask(self, key, dsk, state):
        self.state = state

    def _finish(self, dsk, state, errored):
        self._running = False
        self.timer.join()
        elapsed = default_timer() - self.start_time
        self.last_duration = elapsed
        if not errored:
            self.model.percent = 100
            self.model.elapsed = elapsed
        else:
            raise errored

    def _timer_func(self):
        while self.running:
            elapsed = default_timer() - self.start_time
            if elapsed > self.dt:
                self._update(elapsed)
            time.sleep(self.dt)

    def _update(self, elapsed):
        s = self.state
        if not s:  # tracker was not attached to dask correctly
            self.model.percent = 0
            return
        ndone = len(s["finished"])
        ntasks = sum(len(s[k])
                     for k in ["ready", "waiting", "running"]) + ndone
        pct = int(ndone / ntasks if ntasks else 0)

        if ndone < ntasks:
            self.model.percent = pct
            self.model.elapsed = elapsed


def subset_process_func(request_args, mq, outpath):
    mq.put('startup')  # startup sync message

    # Fixme: couldn't all this figure out the archive stuff be done ahead of time?
    #        the client is never going to know the archive dir, so it's not request specific.
    # No, it's not request specific. It is provided because the subprocess made with 'spawn' does not
    # retain the main process's libgoods config, so the archive_dir needs to be passed in and set here.
    if request_args.get('libgoods_archive', None):
        mq.put('libgoods archive reqested: '+ request_args.get('libgoods_archive').__str__())

    # if libgoods.config.archive_dir does not exist, but a libgoods_archive is provided, use that
    if (libgoods.config.archive_dir is None):
        if request_args.get('libgoods_archive', None):
            libgoods.config.archive_dir = request_args.get('libgoods_archive')
            mq.put('set libgoods archive dir to: ' +
                   request_args.get('libgoods_archive').__str__())
            request_args.pop('libgoods_archive', None)
        else:
            mq.put('config.libgoods_archive not set')
    else:
        mq.put('libgoods.config.archive_dir: ' + libgoods.config.archive_dir.__str__())

    #pop libgoods_archive from request_args since it's not a valid arg for get_model_subset
    request_args.pop('libgoods_archive', None)

    try:
        # raise ValueError('test error')
        result = api.get_model_subset(**request_args)
        mq.put('subset_complete')
        mq.put(result.ds.nbytes or result.size())
        try:
            mq.get(60)  # wait for reconfirmation if needed (e.g. if subset is too large)
        except queue.Empty:
            mq.put('error')
            mq.put('Subset process failed to receive reconfirmation within timeout')
            return
        result.write_nc(outpath)
        mq.put('success')
        mq.put(result)
    except Exception as e:
        mq.put('error')
        mq.put(repr(e), block=True, timeout=5)
        raise
