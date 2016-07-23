from AsyncHttpServer import AsyncHttpHandler, AsyncSocketServer
import logging

class AsyncRoutedHttpHandler(AsyncHttpHandler):
    """ A request handler for the HTTP protocol that supports automatic routing.

    Register handler methods to this class. When receiving a request, a matching handler method will be found and called
    with the request. If no handler method is found, an error 501 is returned to the requester.
    """

    def __init__(self, sock, address, routes):
        """ Create a new instance.

        sock -- the socket
        address -- the (host, port) tuple (only used for logging)
        routes -- a map containing the routes. See set_routes for more information.
        """
        super().__init__(sock, address)
        self.routes = routes

    def handle_any_request(self, request):
        for uri_pattern, handler_method in self.routes[ request.command ]:
            match = uri_pattern.match( request.path )
            if match:
                self.logger.debug('Handling request %s with method %s.%s'
                    % (request.path, handler_method.__module__, handler_method.__name__))
                handler_method( request, *match.groups() )
                return
        request.send_error(404, "Not found: %r" % request.path)

    def set_routes(routes):
        """ Sets the routes for this handler.

        routes -- a map with the supported routes. The keys to this map are the HTTP method. Each entry in the map MUST
        be a tuple (regex, method), whereby regex is the regex used to match the URI in the request, and method is the
        method that will be called when the regex matches. The first matching regex is selected.

        The regex can contain groups. The matched values of these groups will be passed into the method as arguments.
        The method MUST have the following signature: method(request, params...). The request parameter will be an
        object of the AsyncHttpServer.Request class, params MUST match the number of groups in the regex.
        """
        self.routes = routes

    @staticmethod
    def get_factory_with_routes(myroutes):
        """ Create a factory for creating handlers

        myroutes -- the routes that will be given to all instantiated handlers.
        """
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
        request.write_response_payload( b'method2 called with argument ' + val.encode('utf-8') )

    register_route('/api/?', method1, 'GET' )
    register_route('/api/(\d+)/?', method2, 'POST')

    server = AsyncSocketServer( ('localhost', 5000), AsyncRoutedHttpHandler.get_factory_with_routes( routes ) )
    server.start()