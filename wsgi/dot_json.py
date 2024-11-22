# File name: dot_json.py

import sqlite3
import tempfile
import os
import signal
from wsgiref.simple_server import make_server, WSGIServer
from eralchemy import render_er
from mimetypes import MIME_TYPES  # Import shared MIME types

class TimeoutWSGIServer(WSGIServer):
    """WSGIServer with timeout support."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 1  # 1 second timeout for polling

def application(environ, start_response):
    method = environ['REQUEST_METHOD']
    path = environ['PATH_INFO']
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, path.lstrip('/'))

    if method == 'OPTIONS':
        start_response('200 OK', [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type'),
        ])
        return [b'']

    if method == 'GET':
        file_ext = os.path.splitext(file_path)[1]
        mime_type = MIME_TYPES.get(file_ext)

        if mime_type and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            start_response('200 OK', [
                ('Access-Control-Allow-Origin', '*'),
                ('Content-Type', mime_type),
                ('Content-Length', str(len(content))),
            ])
            return [content]
        else:
            start_response('404 Not Found', [
                ('Access-Control-Allow-Origin', '*'),
                ('Content-Type', 'text/plain'),
            ])
            return [b"File not found"]

    if method == 'POST':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(content_length).decode('utf-8')

            if not body.strip():
                raise ValueError("Received SQL query is empty.")

            temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            temp_db_name = temp_db.name
            temp_db.close()

            temp_dot_json = tempfile.NamedTemporaryFile(suffix=".dot_json", delete=False)
            temp_dot_json_name = temp_dot_json.name
            temp_dot_json.close()

            connection = sqlite3.connect(temp_db_name)
            cursor = connection.cursor()
            cursor.executescript(body)
            connection.commit()
            connection.close()

            render_er(f"sqlite:///{temp_db_name}", temp_dot_json_name)

            with open(temp_dot_json_name, "rb") as dot_json_file:
                dot_json_data = dot_json_file.read()

            start_response('200 OK', [
                ('Access-Control-Allow-Origin', '*'),
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(dot_json_data))),
            ])
            return [dot_json_data]

        except Exception as e:
            error_message = f"Error: {e}"
            start_response('500 Internal Server Error', [
                ('Access-Control-Allow-Origin', '*'),
                ('Content-Type', 'text/plain; charset=utf-8'),
            ])
            return [error_message.encode('utf-8')]

    else:
        start_response('405 Method Not Allowed', [
            ('Access-Control-Allow-Origin', '*'),
            ('Content-Type', 'text/plain'),
        ])
        return [b"Only POST and GET methods are supported."]

def run_server():
    global server
    port = 18080
    server = make_server('', port, application, server_class=TimeoutWSGIServer)
    print(f"Serving on port {port}... (Press Ctrl+C to stop)")

    try:
        while True:
            server.handle_request()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        server.shutdown()
        print("Server stopped.")

if __name__ == '__main__':
    run_server()