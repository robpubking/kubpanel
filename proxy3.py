import socket
import threading
import select
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

class SimpleProxyHandler(BaseHTTPRequestHandler):
    def do_CONNECT(self):
        # Handle HTTPS CONNECT method
        host, port = self.path.split(':')
        port = int(port)
        print(f"CONNECT to {host}:{port}")

        try:
            # Connect to the target server
            remote_sock = socket.create_connection((host, port))
            self.send_response(200, 'Connection established')
            self.end_headers()

            # Start bidirectional data transfer
            sockets = [self.connection, remote_sock]
            while True:
                (recv, _, error) = select.select(sockets, [], sockets, 3)
                if error:
                    break
                for sock in recv:
                    data = sock.recv(8192)
                    if not data:
                        break
                    if sock is self.connection:
                        remote_sock.sendall(data)
                    else:
                        self.connection.sendall(data)
        finally:
            self.connection.close()
            remote_sock.close()

    def do_GET(self):
        # Handle HTTP GET method
        url = urlparse(self.path)
        host = url.hostname
        port = url.port or 80
        path = url.path or '/'
        if url.query:
            path += '?' + url.query

        print(f"GET to {host}:{port}{path}")

        try:
            # Connect to the target server
            remote_sock = socket.create_connection((host, port))
            remote_sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())

            # Relay the response back to the client
            while True:
                data = remote_sock.recv(8192)
                if not data:
                    break
                self.wfile.write(data)
        finally:
            self.connection.close()
            remote_sock.close()

    def do_POST(self):
        # Handle HTTP POST method
        url = urlparse(self.path)
        host = url.hostname
        port = url.port or 80
        path = url.path or '/'
        if url.query:
            path += '?' + url.query

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        print(f"POST to {host}:{port}{path}")

        try:
            # Connect to the target server
            remote_sock = socket.create_connection((host, port))
            remote_sock.sendall(f"POST {path} HTTP/1.1\r\nHost: {host}\r\nContent-Length: {content_length}\r\nConnection: close\r\n\r\n".encode() + post_data)

            # Relay the response back to the client
            while True:
                data = remote_sock.recv(8192)
                if not data:
                    break
                self.wfile.write(data)
        finally:
            self.connection.close()
            remote_sock.close()

def run(server_class=ThreadedHTTPServer, handler_class=SimpleProxyHandler, port=38989):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting proxy server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run() 

