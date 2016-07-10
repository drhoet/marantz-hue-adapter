from AsyncHttpServer import AsyncHttpHandler, AsyncSocketServer
import logging, re, inspect

routes = {}

def register_route(uri_pattern, handler_method, http_verb = 'GET'):
    if not http_verb in routes:
        routes[http_verb] = []
    if not uri_pattern.startswith('^'):
        uri_pattern = '^' + uri_pattern
    if not uri_pattern.endswith('$'):
        uri_pattern = uri_pattern + '$'

    compiled_pattern = re.compile(uri_pattern)
    sig = inspect.signature( handler_method )
    if compiled_pattern.groups + 1 != len(sig.parameters):
        raise Exception('pattern %s cannot be applied to method %s.%s: argument count doesn\'t match regex group count' % (uri_pattern, handler_method.__module__, handler_method.__name__))
    routes[http_verb].append( (compiled_pattern, handler_method) )


class AsyncRoutedHttpHandler(AsyncHttpHandler):

    def __init__(self, sock, address, routes):
        super().__init__(sock, address)
        self.routes = routes

    def handle_any_request(self, request):
        for uri_pattern, handler_method in self.routes[ request.command ]:
            match = uri_pattern.match( request.path )
            if match:
                handler_method( request, *match.groups() )
                return
        request.send_error(404, "Not found: %r" % request.path)

    @staticmethod
    def get_factory_with_routes(myroutes):
        def factory_method(sock, address):
            return AsyncRoutedHttpHandler(sock, address, myroutes)
        return factory_method

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s' )

    def async_routed_http_handler_factory( sock, address ):
        return AsyncRoutedHttpHandler(sock, address, routes)
	
    def method1(request):
        request.send_response(200, 'OK')
        request.send_header('Connection', 'close')
        request.write_response_payload( b'method1 called' )


    def method2(request, val):
        request.send_response(200, 'OK')
        request.send_header('Connection', 'close')
        request.write_response_payload( b'method2 called with argument ' + val.encode('utf-8') ) #TODO fixme: encodings

    register_route('/api/?', method1, 'GET' )
    register_route('/api/(\d+)/?', method2, 'POST')

    server = AsyncSocketServer( ('localhost', 5000), AsyncRoutedHttpHandler.get_factory_with_routes( routes ) )
    server.start()