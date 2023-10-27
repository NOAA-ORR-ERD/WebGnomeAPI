"""
Views for the Substance objects.
"""
import logging
import ujson

from pyramid.response import Response
from pyramid.view import view_config

from cornice import Service

from webgnome_api.common.views import (cors_response,
                                       get_object,
                                       create_object,
                                       update_object,
                                       cors_policy,
                                       switch_to_existing_session)

log = logging.getLogger(__name__)

substance = Service(name='substance', path='/substance*obj_id',
                    description="Substance API", cors_policy=cors_policy)

implemented_types = ('gnome.spills.substance.GnomeOil',
                     'gnome.spills.substance.NonWeatheringSubstance'
                     )


@substance.get()
def get_substance(request):
    '''Returns a Gnome Substance object in JSON.'''
    return get_object(request, implemented_types)


@substance.post()
def create_substance(request):
    '''Creates a Gnome Substance object.'''
    return create_object(request, implemented_types)


@substance.put()
def update_substance(request):
    '''Updates a Gnome Substance object.'''
    return update_object(request, implemented_types)


@view_config(route_name='substance_upload', request_method='OPTIONS')
def substance_upload_options(request):
    return cors_response(request, request.response)


@view_config(route_name='substance_upload', request_method='POST')
def upload_substance(request):
    switch_to_existing_session(request)
    log_prefix = f'req({id(request)}): upload_substance():'
    log.info(f'>>{log_prefix}')

    file_list = request.POST.pop('file_list')
    file_list = ujson.loads(file_list)
    name = request.POST.pop('name')
    file_name = file_list[0]

    log.info(f'  {log_prefix} {file_name=}, {name=}')

    substance_type = request.POST.pop('obj_type', [])

    substance_json = {
        'obj_type': substance_type,
        'filename': file_name,
        'name': name
    }

    request.body = ujson.dumps(substance_json).encode('utf-8')

    substance_obj = create_substance(request)
    resp = Response(ujson.dumps(substance_obj))

    log.info(f'<<{log_prefix}')
    return cors_response(request, resp)
