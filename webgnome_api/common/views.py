"""
Common Gnome object request handlers.
"""
import os
import sys
import traceback
import ujson
import uuid
import logging

from threading import current_thread

from pyramid.settings import asbool
from pyramid.interfaces import ISessionFactory
from pyramid.response import FileResponse
from pyramid.httpexceptions import (HTTPBadRequest,
                                    HTTPNotFound,
                                    HTTPInsufficientStorage,
                                    HTTPUnsupportedMediaType,
                                    HTTPNotImplemented)

from .system_resources import (get_free_space,
                               get_size_of_open_file,
                               write_to_file)
from .helpers import (JSONImplementsOneOf,
                      FQNamesToList,
                      PyClassFromName)

from .common_object import (CreateObject,
                            UpdateObject,
                            RegisterObject,
                            ObjectImplementsOneOf,
                            obj_id_from_url,
                            obj_id_from_req_payload,
                            get_session_dir,
                            get_persistent_dir)

from .session_management import (get_session_objects,
                                 get_session_object,
                                 acquire_session_lock)

cors_policy = {'credentials': True,
               'headers': ('Content-Disposition',),
               }

log = logging.getLogger(__name__)

web_ser_opts = {'raw_paths': False}


def can_persist(funct):
    '''
        This is a decorator function intended to short-circuit any views
        that service persistent upload information if the server is not
        configured to do so.
    '''
    def helper(request):
        if ('can_persist_uploads' in list(request.registry.settings.keys()) and
                asbool(request.registry.settings['can_persist_uploads'])):
            return funct(request)
        else:
            raise cors_exception(request, HTTPNotImplemented)

    return helper


def cors_exception(request, exception_class, with_stacktrace=False,
                   title=None, explanation=None):
    depth = 2
    http_exc = exception_class()

    if title is not None:
        http_exc.title = title

    if explanation is not None:
        http_exc.explanation = explanation

    hdr_val = request.headers.get('Origin')
    if hdr_val is not None:
        http_exc.headers.add('Access-Control-Allow-Origin', hdr_val)
        http_exc.headers.add('Access-Control-Allow-Credentials', 'true')

    json_exc = json_exception(depth, with_stacktrace)
    if json_exc is not None:
        http_exc.json_body = json_exc
    if ('develop_mode' in list(request.registry.settings.keys()) and
            asbool(request.registry.settings['develop_mode'])):
        if with_stacktrace:  # remove false to use
            pass
            import pdb
            pdb.post_mortem(sys.exc_info()[2])

    return http_exc


def json_exception(depth, with_stacktrace=False):
    _, exc_value, exc_traceback = sys.exc_info()

    if exc_value is not None:
        exc_json = {'exc_type': exc_value.__class__.__name__,
                    'message': traceback.format_exception_only(_, exc_value)
                    }

        if with_stacktrace:
            tb = traceback.extract_tb(exc_traceback)

            if len(tb) > depth:
                exc_json['traceback'] = [_trace_item(*i) for i in tb[-depth:]]
            else:
                exc_json['traceback'] = [_trace_item(*i) for i in tb]

        return exc_json
    else:
        return None


def _trace_item(filename, lineno, function, text):
    return {'file': filename,
            'lineno': lineno,
            'function': function,
            'text': text}


def cors_response(request, response):
    hdr_val = request.headers.get('Origin')
    if hdr_val is not None:
        response.headers.add('Access-Control-Allow-Origin', hdr_val)
        response.headers.add('Access-Control-Allow-Credentials', 'true')

    req_headers = request.headers.get('Access-Control-Request-Headers')
    if req_headers is not None:
        response.headers.add('Access-Control-Allow-Headers', req_headers)

    req_method = request.headers.get('Access-Control-Request-Method')
    if req_method is not None:
        response.headers.add('Access-Control-Allow-Methods',
                             ','.join((req_method, 'OPTIONS')))

    return response


def cors_file_response(request, path):
    file_response = FileResponse(path)

    hdr_val = request.headers.get('Origin')
    if hdr_val is not None:
        file_response.headers.add('Access-Control-Allow-Origin', hdr_val)
        file_response.headers.add('Access-Control-Allow-Credentials', 'true')

    return file_response


def get_object(request, implemented_types):
    '''Returns a Gnome object in JSON.'''
    obj_id = obj_id_from_url(request)

    if obj_id is None:
        return get_specifications(request, implemented_types)
    else:
        obj = get_session_object(obj_id, request)
        if obj:
            if ObjectImplementsOneOf(obj, implemented_types):
                return obj.serialize(options=web_ser_opts)
            else:
                raise cors_exception(request, HTTPUnsupportedMediaType)
        else:
            raise cors_exception(request, HTTPNotFound)


def get_specifications(request, implemented_types):
    specs = {}
    for t in implemented_types:
        try:
            name = FQNamesToList((t,))[0][0]
            cls = PyClassFromName(t)
            if cls:
                update = cls._schema().get_nodes_by_attr('update')
                read = cls._schema().get_nodes_by_attr('read_only')
                spec = dict([(n, None) for n in update + read])
                spec['obj_type'] = t
                specs[name] = spec
        except ValueError:
            raise cors_exception(request, HTTPNotImplemented)
    return specs


def delete_object(request):
    # INCOMPLETE DO NOT USE
    '''Deletes a Gnome object from both the active model and object registry'''
    log_prefix = 'req({0}): delete_object():'.format(id(request))
    log.info('>>' + log_prefix)


def create_object(request, implemented_types):
    '''Creates a Gnome object.'''
    log_prefix = 'req({0}): create_object():'.format(id(request))
    log.info('>>' + log_prefix)

    try:
        json_request = ujson.loads(request.body)
    except Exception:
        raise cors_exception(request, HTTPBadRequest)

    if not JSONImplementsOneOf(json_request, implemented_types):
        raise cors_exception(request, HTTPNotImplemented)

    session_lock = acquire_session_lock(request)
    log.info('  {} session lock acquired (sess:{}, thr_id: {})'
             .format(log_prefix, id(session_lock), current_thread().ident))

    try:
        log.info(request.session.session_id)
        log.info('  ' + log_prefix + 'creating ' + json_request['obj_type'])
        obj = CreateObject(json_request, get_session_objects(request))
        RegisterObject(obj, request)
    except Exception:
        raise cors_exception(request, HTTPUnsupportedMediaType,
                             with_stacktrace=True)
    finally:
        session_lock.release()
        log.info('  {} session lock released (sess:{}, thr_id: {})'
                 .format(log_prefix, id(session_lock), current_thread().ident))

    log.info('<<' + log_prefix)

    return obj.serialize(options=web_ser_opts)


def update_object(request, implemented_types):
    '''Updates a Gnome object.'''
    log_prefix = 'req({0}): update_object():'.format(id(request))
    log.info('>>' + log_prefix)

    try:
        json_request = ujson.loads(request.body)
    except Exception:
        raise cors_exception(request, HTTPBadRequest)

    if not JSONImplementsOneOf(json_request, implemented_types):
        raise cors_exception(request, HTTPNotImplemented)

    obj = get_session_object(obj_id_from_req_payload(json_request),
                             request)
    if obj:
        session_lock = acquire_session_lock(request)
        log.info('  {} session lock acquired (sess:{}, thr_id: {})'
                 .format(log_prefix, id(session_lock), current_thread().ident))

        try:
            UpdateObject(obj, json_request, get_session_objects(request))
        except Exception:
            raise cors_exception(request, HTTPUnsupportedMediaType,
                                 with_stacktrace=True)
        finally:
            session_lock.release()
            log.info('  {} session lock acquired (sess:{}, thr_id: {})'
                     .format(log_prefix, id(session_lock),
                             current_thread().ident))
    else:
        raise cors_exception(request, HTTPNotFound)

    log.info('<<' + log_prefix)
    return obj.serialize(options=web_ser_opts)


def switch_to_existing_session(request):
    '''
    For some reason, the multipart form does not contain
    a session cookie, and Naomi so far has not been able to explicitly
    set it.

    So this allows us to re-establish contact with a session
    before processing form data, if the session ID is passed in as hidden
    POST content.
    '''
    redis_session_id = request.POST['session']

    if redis_session_id.encode('utf-8') in list(request.session.redis.keys()):
        def get_specific_session_id(redis, timeout, serialize, generator,
                                    session_id=redis_session_id,
                                    **kwargs):
            return session_id

        factory = request.registry.queryUtility(ISessionFactory)
        request.session = factory(request,
                                  new_session_id_func=get_specific_session_id)
        request.session.do_persist()

        if request.session.session_id != redis_session_id:
            log.error(f'request session_id ({request.session.session_id})'
                      ' != '
                      f'redis_session_id ({redis_session_id})')
            raise cors_response(request,
                                HTTPBadRequest('multipart form request '
                                               'could not re-establish session'
                                               ))


def process_upload(request, field_name):
    switch_to_existing_session(request)

    upload_dir = get_session_dir(request)
    max_upload_size = eval(request.registry.settings['max_upload_size'])

    persist_upload = asbool(request.POST.get('persist_upload', False))

    if 'can_persist_uploads' in list(request.registry.settings.keys()):
        can_persist = asbool(request.registry.settings['can_persist_uploads'])
    else:
        can_persist = False

    log.info('save_file_dir: {}'.format(upload_dir))
    log.info('max_upload_size: {}'.format(max_upload_size))

    log.info('persist_upload?: {}'.format(persist_upload))
    log.info('can_persist?: {}'.format(can_persist))

    input_file = request.POST[field_name].file
    file_name, unique_name = gen_unique_filename(request.POST[field_name]
                                                 .filename)
    file_path = os.path.join(upload_dir, unique_name)

    size = get_size_of_open_file(input_file)
    log.info('Incoming file size: {}'.format(size))

    if size > max_upload_size:
        raise cors_response(request, HTTPBadRequest(
            f'file is too big!  Max size = {max_upload_size}'
        ))

    if size >= get_free_space(upload_dir):
        raise cors_response(request, HTTPInsufficientStorage(
            'Not enough space to save the file'
        ))

    write_to_file(input_file, file_path)

    log.info('Successfully uploaded file "{0}"'.format(file_path))

    if persist_upload and can_persist:
        log.info('Persisting file "{0}"'.format(file_path))

        upload_dir = get_persistent_dir(request)
        if size >= get_free_space(upload_dir):
            raise cors_response(request, HTTPInsufficientStorage(
                'Not enough space to persist the file'
            ))

        persistent_path = os.path.join(upload_dir, file_name)

        write_to_file(input_file, persistent_path)

    return file_path, file_name


def activate_uploaded(request):
    '''
        This view is intended to activate a file that has already been
        persistently uploaded.

        We activate it by making a unique copy of it in the session folder.

        persistent file could exist in a sub-folder inside the upload folder.
    '''
    session_dir = get_session_dir(request)
    max_upload_size = eval(request.registry.settings['max_upload_size'])
    log.info('session_dir: {}'.format(session_dir))
    log.info('max_upload_size: {}'.format(max_upload_size))

    upload_dir = get_upload_dir_and_subfolders(get_persistent_dir(request),
                                               request.POST['file-name'])
    log.info('upload_dir: {}'.format(upload_dir))

    file_name, unique_name = gen_unique_filename(request.POST['file-name'])
    src_path = os.path.join(upload_dir, file_name)
    dest_path = os.path.join(session_dir, unique_name)

    if file_name not in os.listdir(upload_dir):
        raise cors_response(request, HTTPBadRequest('File does not exist!'))

    size = os.path.getsize(src_path)
    log.info('File size: {}'.format(size))

    if size >= get_free_space(session_dir):
        # basically we need to make a copy of the file to activate it.
        raise cors_response(request,
                            HTTPInsufficientStorage('Not enough space '
                                                    'to activate the file'))

    write_to_file(src_path, dest_path)

    log.info('Successfully activated file "{0}"'.format(dest_path))

    return dest_path, file_name


def gen_unique_filename(filename_in, upload_dir=None):
    # add uuid to the file name in case the user accidentally uploads
    # multiple files with the same name for different objects.
    if upload_dir:
        existing_files = os.listdir(upload_dir)
        file_name, extension = get_file_name_ext(filename_in)
        fmtstring = file_name + '{0}' + extension
        new_fn = fmtstring.format('')
        i = 1

        while i < 255:
            if new_fn not in existing_files:
                return (file_name + extension, new_fn)
            else:
                new_fn = fmtstring.format(' (' + str(i) + ')')
                i += 1

        raise ValueError('File uploaded too many times')
    else:
        file_name, extension = get_file_name_ext(filename_in)
        return (file_name + extension,
                file_name + '-' + str(uuid.uuid4()) + extension)


def get_file_name_ext(filename_in):
    # in case a path was passed as the name
    base_name = os.path.basename(filename_in)
    file_name, extension = os.path.splitext(base_name)

    return file_name, extension


def get_upload_dir_and_subfolders(upload_dir, file_path):
    '''
        return a path that is the concatenation of a base path and the
        possible sub-directories represented in a file name.
        The up-directory is not allowed.
    '''
    sub_dirs = [p for p in file_path.split(os.sep) if p != '..'][:-1]
    return os.path.join(upload_dir, *sub_dirs)
