"""
    Common Gnome object request handlers.
"""
import os
import shutil
import urllib.request
import ujson
import logging

from collections.abc import Iterable

from gnome.gnomeobject import GnomeId
from gnome.utilities.orderedcollection import OrderedCollection
from gnome.spill_container import SpillContainerPair

from .helpers import FQNamesToDict, PyClassFromName

from webgnome_api.common.session_management import (req_session_is_valid,
                                                    set_session_object,
                                                    get_session_object)

log = logging.getLogger(__name__)


def DeleteObject(id_, all_objects):
    # THIS IS INCOMPLETE DO NOT USES
    if id_ is None:
        raise ValueError('Tried to delete object without an id')

    if id_ in all_objects:
        del all_objects[id_]


def recursive_removal(model, id_):
    sch = model._schema()
    for c in sch.children:
        child_obj = getattr(model, c.name)
        if (hasattr(child_obj, 'id') and hasattr(child_obj, 'obj_type')):
            # child object is a Gnome object
            if child_obj.id == id_:
                model.setattr(c.name, None)
            else:
                recursive_removal(child_obj, id_)
        elif isinstance(child_obj, Iterable) and type(child_obj) is not str:
            # child object is a list of some kind
            for i, obj in enumerate(child_obj):
                if (hasattr(obj, 'id') and hasattr(obj, 'obj_type')):
                    if obj.id_ == id_:
                        del child_obj[i]  # del or set to None?? Risky??
                    else:
                        recursive_removal(obj, id_)


def CreateObject(json_obj, all_objects, deserialize_obj=True):
    '''
        The Main entry point to be used by our views.

        We want to be able to handle nested object payloads, so we need
        to traverse to all leaf objects and update them first
    '''
    otype = json_obj.get('obj_type', None)
    if otype is None:
        raise ValueError('No object type defined in payload')

    py_class = PyClassFromName(otype)

    id_ = json_obj.get('id', None)

    if id_ not in all_objects:
        return py_class.deserialize(json_obj, all_objects)
    else:
        return all_objects[id_]


def UpdateObject(obj, json_obj, all_objects, deserialize_obj=True):
    '''
        The Main entry point to be used by our views.

        We want to be able to handle nested object payloads, and this is now
        apparently handled internally by PyGnome.  This gives us a bit of a
        conundrum.

        We have a few contexts to consider for our payload:
        - PyGnome: This is a self contained module that is originally built
                   primarily for scripting.  As such, it has update methods
                   that consider only the context of the PyGnome model
                   structures.  For example, if a shapefile outputter is
                   updated with a filename, it will take the filename at
                   face value.
        - WebGnomeAPI: A web server manages two contexts in regards to
                       information it is persisting.
                       1 - Where is it internally storing the data?
                       2 - How does it present that data to the entity
                           requesting it?
                       The web server will maintain configurable paths in the
                       filesystem for storing temporary session data files and
                       persistent files. So the context can have different
                       behaviors, depending upon where the data is stored,
                       but in the context of a file in a file system, the data
                       will be internally stored at a fully qualified pathname,
                       and will be presented as a partial pathname (URL?)
                       to the requestor.

         This means we need to treat the incoming data such as filenames
         before we pass the data to PyGnome's update method.  It also means
         we need to similarly treat the outgoing data to the requestor.

         It will probably be easiest to handle this in the tween, so look for
         the implementation there.
    '''
    otype = json_obj.get('obj_type', None)
    if otype is None:
        raise ValueError('No object type defined in payload')

    py_class = PyClassFromName(otype)

    id_ = json_obj.get('id', None)

    if id_ not in all_objects:
        new_obj = py_class.deserialize(json_obj, all_objects)
        return new_obj
    else:
        all_objects[id_].update(json_obj, refs=all_objects)

        return all_objects[id_]


def ValueIsJsonObject(value):
    return (isinstance(value, dict) and 'obj_type' in value)


def ObjectId(obj):
    try:
        ident = obj['id']  # JSON Object
    except Exception:
        try:
            ident = obj.id  # Gnome Object
        except Exception:
            ident = id(obj)  # any other object

    return ident


def ObjectExists(value, all_objects):
    return ObjectId(value) in all_objects


def ObjectImplementsOneOf(model_object, obj_types):
    '''
        Here we determine if our python object type is contained within a set
        of implemented object types.

        :param model_obj: python object
        :param obj_types: list of fully qualified object names.
    '''
    if model_object.__class__.__name__ in FQNamesToDict(obj_types):
        return True

    return False


def RegisterObject(obj, request):
    '''
        Recursively register an object plus all contained child objects.
        Registering means we put the object somewhere it can be looked up
        in the Web API.
        We would mainly like to register PyGnome objects.  Others
        we probably don't care about.
    '''
    sequence_types = (list, tuple, OrderedCollection, SpillContainerPair)

    if (isinstance(obj, GnomeId)):
        set_session_object(obj, request)
        log.info(f'registering {obj.name} '
                 f'on session {request.session.session_id}')

    if isinstance(obj, sequence_types):
        for i in obj:
            if (isinstance(i, GnomeId)):
                RegisterObject(i, request)
    elif hasattr(obj, '__dict__'):
        for k in dir(obj):
            attr = None
            try:
                attr = getattr(obj, k)
            except Exception as e:
                log.warning(str(e))

            if ((isinstance(attr, GnomeId) and get_session_object(attr.id, request) is None)
                    or isinstance(attr, sequence_types)):
                RegisterObject(attr, request)


def obj_id_from_url(request):
    '''
        The pyramid URL parser returns a tuple of 0 or more
        matching items, at least when using the * wild card
    '''
    obj_id = request.matchdict.get('obj_id')

    if obj_id is not None and len(obj_id) > 0:
        return obj_id[0]
    else:
        return None


def obj_id_from_req_payload(json_request):
    return json_request.get('id')


def get_session_base_dir(request):
    return os.path.normpath(request.registry.settings['session_dir'])


def get_persistent_dir(request):
    persistent_dir = os.path.normpath(request.registry.settings['persistent_dir'])

    if os.path.isdir(persistent_dir) is False:
        os.makedirs(persistent_dir)

    return persistent_dir


@req_session_is_valid
def get_session_dir(request):
    session_dir = os.path.join(get_session_base_dir(request),
                               request.session.session_id)

    if os.path.isdir(session_dir) is False:
        os.makedirs(session_dir)

    return session_dir


@req_session_is_valid
def list_session_dir(request):
    '''
        Purely diagnostic in intent, we simply list the files in our
        session directory.
    '''
    session_dir = get_session_dir(request)

    if os.path.isdir(session_dir) is True:
        # our session folder exists, clean out any files
        for f in os.listdir(session_dir):
            print(f'\t{f}')


@req_session_is_valid
def clean_session_dir(request):
    session_dir = get_session_dir(request)

    if os.path.isdir(session_dir) is True:
        # our session folder exists, clean out any files
        for f in os.listdir(session_dir):
            try:
                f = os.path.join(session_dir, f)
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
            except Exception:
                pass


def get_file_path(request, json_request=None):
    '''
        take a request/json object and transform it's filename
        attribute into a full path.

        providing the already parsed json will save the need to reprocess
        the json into a dict. if this is already done before calling
        get_file_path passing it along with the request is recommended

        goods: prefix relates to a mounted share between gnome
        and goods uses the goods_dir ini setting

        http or https is a remote file that should be downloaded
        to a temporary directory and the path updated.
        currently should be limited to urls from the goods domain name
        The file will be placed in a session specific directory inside
        model_data_dir
    '''
    goods_dir = request.registry.settings['goods_dir']
    goods_url = request.registry.settings['goods_url']
    session_dir = get_session_dir(request)

    if json_request is None:
        json_request = ujson.loads(request.body)

    if (json_request['filename'].startswith('http') and
            json_request['filename'].find(goods_url) != -1):
        resp = urllib.request.urlopen(json_request['filename'])

        (_remote_dir, fname) = os.path.split(json_request['filename'])

        with open(os.path.join(session_dir, fname), 'wb') as fh:
            while True:
                data = resp.read(1024 * 1024)

                if len(data) == 0:
                    break
                else:
                    fh.write(data)

        json_request['filename'] = fname

    if json_request['filename'].startswith('goods:') and goods_dir != '':
        full_path = os.path.join(goods_dir, json_request['filename'][6:])
    else:
        full_path = os.path.join(session_dir, json_request['filename'])

    return full_path
