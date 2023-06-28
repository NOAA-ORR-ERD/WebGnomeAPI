'''
    Middleware Classes for handling py_gnome functionality
    These will be processes that can massage an incoming request
    so that it will be more easily digestible to py_gnome.
    This will make it so the Web Client doesn't have to work quite as hard.
'''
import os
import regex as re
import base64
import hashlib

import ujson

from webgnome_api.common.common_object import (ValueIsJsonObject,
                                               get_session_dir)


class PyGnomeSchemaTweenFactory(object):
    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry

        # one-time configuration code goes here

    def add_json_key(self, json_request):
        modified = False

        if isinstance(json_request, dict):
            for v in json_request.values():
                if self.add_json_key(v):
                    modified = True
        elif isinstance(json_request, (list, tuple)):
            for v in json_request:
                if self.add_json_key(v):
                    modified = True

        return modified

    def fix_filename(self, request, classname, filename):
        '''
            Decide what a filename path should be based on class criteria, and
            return a 'fixed' path.

            Note: This should be a bit smarter in the future.  Maybe we could
                  formalize a simple grammar for deciding whether a file exists
                  in the session folder or the persistent folder.
        '''
        session_dir = get_session_dir(request)

        if classname.split('.')[-1].lower().find('output') != -1:
            # outputter classes will have a special place in the session
            # folder
            full_path = os.path.join(session_dir, 'output',
                                     classname, filename)
        else:
            # otherwise we make no assumptions
            full_path = filename

        return full_path

    def fix_filename_attrs(self, request, json_data):
        '''
            Recurse through our json data structures, and fix any filename
            attributes to have a full path to the resource in the session
            folder.
        '''
        if ValueIsJsonObject(json_data):
            for k, v in list(json_data.items()):
                if k == 'filename':
                    json_data[k] = self.fix_filename(request,
                                                     json_data['obj_type'],
                                                     v)
                else:
                    self.fix_filename_attrs(request, v)
        elif isinstance(json_data, (list, tuple)):
            for _i, v in enumerate(json_data):
                self.fix_filename_attrs(request, v)
        elif isinstance(json_data, set):
            for _i, v in enumerate(list(json_data)):
                self.fix_filename_attrs(request, v)

    def generate_short_session_id(self, request):
        if hasattr(request, 'session'):
            hasher = hashlib.sha1(request.session.session_id.encode('utf-8'))
            request.session_hash = (base64.urlsafe_b64encode(hasher.digest())
                                    .decode())

    def before_the_handler(self, request):
        # code to be executed for each request
        # BEFORE the actual application code
        # goes here
        if ('CONTENT_TYPE' in request.environ and
                request.environ['CONTENT_TYPE'][:16] == 'application/json' and
                request.body):
            json_request = ujson.loads(request.body)
            # json_request = self.sanitizeJSON(json_request)

            self.add_json_key(json_request)
            self.fix_filename_attrs(request, json_request)

            # TODO: The tween seems like a logical place to do
            #       Preprocessing on a request.
            #       But it seems like a wasteful use of processing
            #       to evaluate our JSON request, update some content,
            #       and then turn it back into a string.
            #       I tried just leaving it as a JSON object, but the
            #       request body doesn't accept anything but a string.
            request.body = ujson.dumps(json_request).encode('utf-8')

        self.generate_short_session_id(request)

    def after_the_handler(self, response):
        # code to be executed for each request
        # AFTER the actual application code
        # goes here
        pass

    HTMLsanitize = re.compile(r'["\'&]')

    def sanitize_string(self, s):
        # basic HTML string sanitization
        return re.sub(self.HTMLsanitize, '_', s)

    def sanitizeJSON(self, json_):
            # response should be a JSON structure
            # Removes dangerous HTML from the body of the response
            if isinstance(json_, str):
                return self.sanitize_string(json_)
            elif isinstance(json_, list):
                # array case
                for j, val in enumerate(json_):
                    json_[j] = self.sanitizeJSON(val)
            else:
                # object case
                if hasattr(json_, 'items'):
                    for k, v in json_.items():
                        json_[k] = self.sanitizeJSON(v)

            return json_

    def __call__(self, request):
        self.before_the_handler(request)

        response = self.handler(request)

        self.after_the_handler(response)

        return response
