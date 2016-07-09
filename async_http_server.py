import logging
import asyncore
import asynchat
import socket
from io import BytesIO
from http.server import BaseHTTPRequestHandler

class SocketServer(asyncore.dispatcher):

    def __init__(self, address, handler):
        asyncore.dispatcher.__init__(self)
        
        self.logger = logging.getLogger('SocketServer')
        self.logger.info('Opening socket')

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind( address )
        self.address = self.socket.getsockname()
        self.listen(1)

        self.address = address
        self.handler = handler

        self.logger.info('Listening to connections')        
        return

    def handle_accept(self):
        # Called when a client connects to our socket
        conn, address = self.accept()
        self.logger.info('Accepting connection on %s', address)
        self.handler(conn, address)
        return

class Request(BaseHTTPRequestHandler):

    def __init__(self, address):
        self.client_address = address
        self.rfile = BytesIO()
        self.wfile = BytesIO()
        self.command = None
        self.request_payload = ''

    def parse_request_header(self):
        self.rfile.seek(0)
        self.raw_requestline = self.rfile.readline()
        super().parse_request()

        self.required_data_length = int(self.headers.get('content-length', '0'))
        self.complete = self.required_data_length == 0
        self.rfile = BytesIO() # clear

    def parse_request_payload(self):
        self.request_payload = bytearray( self.rfile.getbuffer() )
        self.complete = True

    def write_response_payload(self, payload):
        self.send_header('Content-Length', len(payload))
        self.end_headers()
        self.wfile.write( payload )

class HttpHandler(asynchat.async_chat):

    def __init__(self, sock, address):
        asynchat.async_chat.__init__(self, sock)
        self.logger = logging.getLogger('HttpHandler')

        self.request = Request(address)
        self.set_terminator( b'\r\n\r\n' ) #end of headers

    def collect_incoming_data(self, data):
        self.request.rfile.write( data )

    def found_terminator(self):
        if not self.request.command:
            self.request.parse_request_header() #TODO: handle error here

            if not self.request.complete:
                self.set_terminator( self.request.required_data_length ) #listen to the end of the data

        else:
            self.request.parse_request_payload()

        if self.request.complete:
            mname = 'do_' + self.request.command
            if not hasattr(self, mname):
                self.request.send_error(501, "Unsupported method (%r)" % self.request.command)
                return

            method = getattr(self, mname)
            method(self.request)

            self.push( bytearray( self.request.wfile.getbuffer() ) )
            self.close_when_done()

    def do_GET(self, request):
        self.logger.debug('Default GET method. Overwrite me.')
        request.send_response(200, 'OK')
        request.send_header('Connection', 'close')
        request.write_response_payload(b'Default GET method. Overwrite me.')
        pass

    def do_POST(self, request):
        self.logger.debug('Default POST method. Overwrite me.')
        request.send_response(200, 'OK')
        request.send_header('Connection', 'close')
        request.write_response_payload( b'Default POST method. Overwrite me.' )
        pass

logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s' )

server = SocketServer( ('localhost', 5000), HttpHandler )

try:
    asyncore.loop(timeout=2)
except KeyboardInterrupt:
    print("Crtl+C pressed. Shutting down.")