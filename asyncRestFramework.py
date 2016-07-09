from asyncHttpServer import AsyncHttpHandler, AsyncSocketServer
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
    if compiled_pattern.groups + 1 != len(inspect.signature( handler_method ).parameters):
        raise Exception('pattern group count does not match method %s', handler_method)
    routes[http_verb].append( (compiled_pattern, handler_method) )


class AsyncRestHandler(AsyncHttpHandler):

    def handle_any_request(self, request):
        for uri_pattern, handler_method in routes[ request.command ]:
            match = uri_pattern.match( request.path )
            if match:
                handler_method( request, *match.groups() )
                return
        request.send_error(404, "Not found: %r" % request.path)


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s' )

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

    server = AsyncSocketServer( ('localhost', 5000), AsyncRestHandler )
    server.start()