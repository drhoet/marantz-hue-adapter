import logging
import asyncore
import asynchat
import socket
from io import BytesIO
from http.server import BaseHTTPRequestHandler

class AsyncSocketServer(asyncore.dispatcher):
    """ Socket server based on the asyncore module

    Create an instance of this class on the port / interface you want it.
    Then call the start() method to start the async loop
    """

    def __init__(self, address, handler):
        """ Create a new instance of the server

        address -- a tuple (host, port) to listen on
        handler -- the connection handler. Whenever a client connects, a new handler will be created to handle the
            connection.
        """
        asyncore.dispatcher.__init__(self)
        
        self.logger = logging.getLogger('AsyncSocketServer')

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind( address )
        self.address = self.socket.getsockname()
        self.listen(1)

        self.address = address
        self.handler = handler

        self.logger.info('Listening to connections on %s:%d' % address)

    def handle_accept(self):
        # Called when a client connects to our socket
        conn, address = self.accept()
        self.logger.info('Accepting connection on %s', address)
        self.handler(conn, address)

    def start(self):
        """ Starts the server by running the asyncore loop."""
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            print("Crtl+C pressed. Shutting down.")        

class Request(BaseHTTPRequestHandler):
    """ A class representing a request.

    Use the rfile and wfile streams to read and write it.
    The command property contains the http verb
    The path property contains the uri
    The headers property can be used to read the headers (e.g. headers.get('content-lenght', default_val))
    The payload property contains the request payload

    Useful methods:
    send_header(key, value) -- adds a header to the response
    end_headers() -- ends the header section of the request. No more headers should be added after this point
    write_response_payload( payload ) -- adds a payload to the response. See also more info below.

    See also the documentation of BaseHTTPRequestHandler for more information.
    """

    def __init__(self, address):
        self.client_address = address
        self.rfile = BytesIO()
        self.wfile = BytesIO()
        self.command = None
        self.request_payload = ''

    def _parse_request_header(self):
        self.rfile.seek(0)
        self.raw_requestline = self.rfile.readline()

        if super().parse_request():
            self.required_data_length = int(self.headers.get('content-length', '0'))
            self.complete = self.required_data_length == 0
            self.rfile = BytesIO() # clear
            return True
        else:
            return False

    def _parse_request_payload(self):
        self.request_payload = bytearray( self.rfile.getbuffer() )
        self.complete = True

    def write_response_payload(self, payload):
        """ Writes a response

        Writes a response to the output stream. This method also adds the Content-Length header and ends the headers
        section. Therefore, make sure you have written all headers before calling this method!

        payload -- The bytes to be added to the payload.
        """
        self.send_header('Content-Length', len(payload))
        self.end_headers()
        self.wfile.write( payload )

class AsyncHttpHandler(asynchat.async_chat):
    """ A request handler for the HTTP protocol.

    When receiving a request, after parsing it completely, it will call a method do_METHOD, where METHOD is the
    HTTP-method of the request (e.g. do_GET or do_POST). If no such method exists, it will fall back to the method
    handle_any_request. If that method also doesn't exist, an error 501 is returned to the requester.

    The do_METHOD methods should have the signature def do_METHOD(self, request), where request is an instance of the
    Request class.
    """

    def __init__(self, sock, address):
        super().__init__(sock)
        self.logger = logging.getLogger('AsyncHttpHandler')

        self.request = Request(address)
        self.set_terminator( b'\r\n\r\n' ) #end of headers

    def collect_incoming_data(self, data):
        self.request.rfile.write( data )

    def found_terminator(self):
        if not self.request.command: # parse headers
            if self.request._parse_request_header():
                if not self.request.complete:
                    self.set_terminator( self.request.required_data_length ) #listen to the end of the data
            else:
                self.push( bytearray( self.request.wfile.getbuffer() ) ) #make sure to push errors to the client
                self.close_when_done()
                return
        else: # parse payload
            self.request._parse_request_payload()

        if self.request.complete: # execute request
            try:
                mname = 'do_' + self.request.command
                if not hasattr(self, mname):
                    if hasattr(self, 'handle_any_request'):
                        mname = 'handle_any_request'
                    else:
                        self.request.send_error(501, "Unsupported method (%r)" % self.request.command)
                        return

                method = getattr(self, mname)
                method(self.request)
            finally:
                self.push( bytearray( self.request.wfile.getbuffer() ) ) #make sure to push any response to the client
                self.close_when_done()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s' )

    server = AsyncSocketServer( ('localhost', 5000), AsyncHttpHandler )
    server.start()