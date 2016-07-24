import logging
import asynchat
import socket
from io import BytesIO

class AsyncSocketHandler(asynchat.async_chat):
    """ A request handler for a plain socket connection.

    Subclass this and implement your logic in the command_received method.
    """

    def __init__(self, address):
        super().__init__()
        self.logger = logging.getLogger('AsyncSocketHandler')
        self.set_terminator( b'\r' )
        self.rfile = BytesIO()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( address )

    def handle_connect(self):
        self.logger.info('Connected!')

    def handle_close(self):
        self.logger.info('Closed!')

    def collect_incoming_data(self, data):
        self.rfile.write( data )

    def command_received(self, command):
        pass

    def found_terminator(self):
        command = self.rfile.getvalue().decode('ascii')
        self.command_received(command)
        self.rfile = BytesIO()

    def push_str(self, str):
        self.push(str.encode('ascii'))
