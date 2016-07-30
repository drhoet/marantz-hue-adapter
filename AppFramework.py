from AsyncHttpServer import AsyncSocketServer
from AsyncRoutedHttpHandler import AsyncRoutedHttpHandler
import logging
import re
import inspect
import asyncore
import sys
import json
import traceback
import codecs
from functools import wraps

class RequestWrapper():

    regex = re.compile('^\s*charset\s*=\s*([\w-]+)\s*$', re.I)

    def __init__(self, request):
        self.wrapped = request
        self.headers = request.headers

        content_type = request.headers.get('content-type', 'charset=iso-8859-1')

        charset = None
        for x in content_type.split(';'):
            m = RequestWrapper.regex.search(x)
            if m:
                charset = m.group(1)
                break
        if not charset:
            charset='iso-8859-1'
        self.data = request.request_payload.decode(charset)


class JsonResponse():

    def __init__(self, content, encoder = None):
        self.content = content
        self.encoder = encoder


class ResponsePusher():

    def can_handle(self, obj):
        return False

    def push(self, request, obj):
        self.send_status_line(request, obj)
        self.send_headers(request, obj)
        self.send_payload(request, obj)

    def send_status_line(self, request, obj):
        request.send_response(200, 'OK')

    def send_headers(self, request, obj):
        request.send_header('Connection', 'close')

    def send_payload(self, request, obj):
        pass


class BytesReponsePusher(ResponsePusher):

    def can_handle(self, obj):
        return isinstance(obj, (bytes, bytearray, memoryview))

    def send_payload(self, request, obj):
        request.write_response_payload( obj )


class StringResponsePusher(BytesReponsePusher):

    def __init__(self, content_type='text/html'):
        self.content_type = content_type

    def can_handle(self, obj):
        return isinstance(obj, (str))

    def send_payload(self, request, obj):
        # can't support multiple charset headers here, since the python library doesn't seem to support it. Would have
        # to implement the header parsing myself to support it...
        charset = request.headers.get('accept-charset', 'iso-8859-1')
        charset = charset.split(',', 1)[0].split(';', 1)[0]
        
        try:
            codecs.lookup(charset)
        except LookupError:
            charset = 'iso-8859-1'

        request.send_header('Content-Type', self.content_type + '; charset=' + charset)
        super().send_payload(request, obj.encode(charset, 'replace') )


class JsonResponsePusher(StringResponsePusher):

    def __init__(self):
        super().__init__('application/json')

    def can_handle(self, obj):
        return isinstance(obj, JsonResponse)

    def send_payload(self, request, obj):
        super().send_payload(request, json.dumps(obj.content, cls=obj.encoder))


class App():
    """ A REST application mini-framework."""

    def __init__(self, name):
        """ Creates a new application with given name."""
        self.name = name
        self.routes = {'GET':[], 'PUT':[], 'DELETE':[]}
        self.response_pushers = [JsonResponsePusher(), StringResponsePusher(), BytesReponsePusher()]

        self.logger = logging.getLogger('App: ' + name)

    def register_route(self, uri_pattern, handler_method, http_verb = 'GET'):
        """ Register a route in the app

        uri_pattern -- a regex with the uri pattern
        handler_method -- the method that will be called if a request with URI matching the uri_pattern is received
        http_verb -- the HTTP verb for which this route will be used
        """
        if not http_verb in self.routes:
            self.routes[http_verb] = []
        if not uri_pattern.startswith('^'):
            uri_pattern = '^' + uri_pattern
        if not uri_pattern.endswith('$'):
            uri_pattern = uri_pattern + '$'

        compiled_pattern = re.compile(uri_pattern)
        sig = inspect.signature( handler_method )
        if compiled_pattern.groups + 1 != len(sig.parameters):
            raise Exception("pattern %s cannot be applied to method %s.%s: argument count doesn't match regex group "
             "count" % (uri_pattern, handler_method.__module__, handler_method.__name__))
        self.routes[http_verb].append( (compiled_pattern, handler_method) )

        self.logger.debug('Registered new route: %s %s -> %s.%s' % (http_verb, uri_pattern, handler_method.__module__,
            handler_method.__name__))

    def push_response(self, request, response_obj):
        """ Pushes a response to the caller

        request -- the request
        response_obj -- the response to be pushed. Supported types are a string and a json object.
        """
        pusher = next( (p for p in self.response_pushers if p.can_handle( response_obj )), None)
        if not pusher:
            raise ValueError('return value cannot be written to response (unexpected type: %s)' % type(response_obj))
        else:
            pusher.push(request, response_obj)

    def route(self, uri_pattern, http_verb='GET'):
        """ Decorator for defining a route.

        Defines the method it decorates as a handler method for requests with given http verb and uri pattern.
        The return value of the decorates method will be pushed to the caller with the push_response() method
        automatically. If any errors happen during the call of the decorated method, an error 500 is pushed to the
        client.
        """
        def register_route_decorator(func):
            
            @wraps(func)
            def write_to_response_decorator(request, *args):
                try:
                    return_val = func(RequestWrapper(request), *args)
                    self.push_response(request, return_val)
                except:
                    traceback.print_exc()
                    request.send_error(500, 'server exception happened')
            
            self.register_route(uri_pattern, write_to_response_decorator, http_verb)
            return func
        return register_route_decorator

    def start(self, host, port, debug):
        """ Starts the app by starting the asyncore loop."""

        self.logger.info('Starting app %s' % self.name)
        server = AsyncSocketServer( (host, port), AsyncRoutedHttpHandler.get_factory_with_routes( self.routes ) )
        server.start()