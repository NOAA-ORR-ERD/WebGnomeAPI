'''
Helper functions to be used by views.
'''
import sys
import logging

import zipfile
import ujson

log = logging.getLogger(__name__)


def update_savefile(file_path, request):
    '''
    Takes a zipfile containing no version.txt and up-converts it
    to 'version 1'.
    This functions purpose is to upgrade save files to maintain compatibility
    after the SpillRefactor upgrades.
    '''
    def Substance_from_ElementType(et_json, water):
        '''
        Takes element type cstruct with a substance, creates an appropriate
        GnomeOil cstruct
        '''
        if 'substance' not in et_json:
            '''
            Note the id of the new cstructs. The ID IS required at this stage,
            because the load process will use it later to establish references
            between objects
            '''
            substance = {
                "obj_type": "gnome.spills.substance.NonWeatheringSubstance",
                "name": "NonWeatheringSubstance",
                "standard_density": 1000.0,
                "initializers": et_json.get('initializers', []),
                "is_weatherable": False,
                "id": "v0-v1-update-id-0"
            }
        else:
            substance = {
                "obj_type": "gnome.spills.gnome_oil.GnomeOil",
                "name": et_json.get('substance', 'Unknown Oil'),
                "initializers": et_json.get('initializers', []),
                "is_weatherable": True,
                "water": water,
                "id": "v0-v1-update-id-1"
            }
            if isinstance(et_json.get('substance', None), dict):
                substance.update(et_json.get('substance'))

        return substance

    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            if 'version.txt' in zf.namelist():
                log.debug('version.txt found')

                with zf.open('version.txt') as vf:
                    v = vf.readline()
                    if v != '0':
                        log.debug('version is not 0')
                        return file_path

            log.debug('updating save file from v0 to v1 (Spill Refactor)')
            water_json = element_type_json = None
            spills = []
            inits = []

            with zipfile.ZipFile(file_path + '.updated', 'w') as new_zf:
                for fname in zf.namelist():
                    buffer = zf.read(fname)
                    with zf.open(fname) as json_file:
                        try:
                            json_ = ujson.load(json_file)
                            if 'obj_type' in json_:
                                if ('Water' in json_['obj_type'] and
                                        'environment' in json_['obj_type'] and
                                        water_json is None):
                                    water_json = (fname, json_)
                                if ('element_type' in json_['obj_type'] and
                                        element_type_json is None):
                                    element_type_json = (fname, json_)
                                    continue  # to skip this file
                                if 'gnome.spills.spill.Spill' in json_['obj_type']:
                                    spills.append((fname, json_))
                                    continue
                                if 'initializers' in json_['obj_type']:
                                    inits.append((fname, json_))
                                    continue
                            new_zf.writestr(fname, buffer)
                        except Exception:
                            new_zf.writestr(fname, buffer)

                # Generate new substance object
                if water_json is None:
                    water_json = (None, None)

                substance = Substance_from_ElementType(element_type_json[1],
                                                       water_json[1])
                substance_fn = substance['name'] + '.json'

                # Write modified and new files to zip
                new_zf.writestr(substance['name'] + '.json',
                                ujson.dumps(substance, indent=True))

                for spill in spills:
                    fn, sp = spill
                    del sp['element_type']
                    sp['substance'] = substance_fn
                    new_zf.writestr(fn, ujson.dumps(sp, indent=True))

                for init in inits:
                    fn, init = init
                    init['obj_type'] = (init['obj_type']
                                        .replace('.elements.', '.'))
                    new_zf.writestr(fn, ujson.dumps(init, indent=True))

        return file_path + '.updated'
    except Exception:
        if ('develop_mode' in list(request.registry.settings.keys()) and
                request.registry.settings['develop_mode'].lower() == 'true'):
            import pdb
            pdb.post_mortem(sys.exc_info()[2])

        raise TypeError('This savefile format is deprecated and '
                        'can not be loaded by WebGNOME')


def FQNameToNameAndScope(fully_qualified_name):
    fqn = fully_qualified_name
    return (list(reversed(fqn.rsplit('.', 1)))
            if fqn.find('.') >= 0
            else [fqn, ''])


def FQNamesToIterList(names):
    for n in names:
        yield FQNameToNameAndScope(n)


def FQNamesToList(names):
    return list(FQNamesToIterList(names))


def FilterFQNamesToIterList(names, name=None, namespace=None):
    for i in FQNamesToIterList(names):
        if ((name and i[0].find(name) >= 0) or
                (namespace and i[1].find(namespace) >= 0)):
            yield i


def FQNamesToDict(names):
    '''
        Takes a list of fully qualified names and turns it into a dict
        Where the object names are the keys.
        (note: dunno if this more useful than the plain dict() method.)
    '''
    return dict(FQNamesToIterList(names))


class PyObjFromJson(object):
    '''
        Generalized method for interpreting a nested data structure of
        dicts, lists, and values, such as that coming from a parsed
        JSON string.  We consume this data structure and represent it
        as a structure of linked python objects.

        So instead of needing to access our data like this:
            json_obj['children'][0]['name']
        we can do this instead:
            json_obj.children[0].name
    '''
    def __init__(self, data):
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        elif isinstance(value, dict):
            return PyObjFromJson(value)
        else:
            return value


def JSONImplementsOneOf(json_obj, obj_types):
    try:
        return not JSONImplementedType(json_obj, obj_types) is None
    except Exception:
        return False


def JSONImplementedType(json_obj, obj_types):
    '''
        Here we determine if our JSON request payload implements an object
        contained within a set of implemented object types.

        I think this is a good place to implement our schema validators,
        but for right now let's just validate that it refers to an object
        type that is implementable.
        The convention we will use is this:
        - Our JSON will be a dictionary
        - This dictionary will contain a key called 'obj_type'
        - Key 'obj_type' will be in the format '<namespace>.<object_name>',
          where:
            - <namespace> refers to the python module namespace where
              the python class definition lives.
            - <object_name> refers to the name of the python class that
              implements the object.
        - This is not currently enforced, but It is understood that all
          other keys of the dictionary will conform to the referred object's
          construction method(s)

        :param json_obj: JSON payload
        :param obj_types: list of fully qualified object names.
    '''
    if not isinstance(json_obj, dict):
        raise ValueError('JSON needs to be a dict')

    if 'obj_type' not in json_obj:
        raise ValueError('JSON object needs to contain an obj_type')

    name = FQNameToNameAndScope(json_obj['obj_type'])[0]
    if name in FQNamesToDict(obj_types):
        return PyClassFromName(json_obj['obj_type'])

    return None


def PyClassFromName(fully_qualified_name):
    name, scope = FQNameToNameAndScope(fully_qualified_name)
    my_module = __import__(scope, globals(), locals(), [str(name)], 0)

    return getattr(my_module, name)
