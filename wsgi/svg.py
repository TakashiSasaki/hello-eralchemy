# File name: svg.py

import sqlite3
import tempfile
import os
import signal
import sys
from wsgiref.simple_server import make_server, WSGIServer
from eralchemy import render_er

# MIMEタイプを拡張子に基づいて設定
MIME_TYPES = {
    '.sql': 'text/plain',
    '.txt': 'text/plain',
    '.svg': 'image/svg+xml',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
}

class TimeoutWSGIServer(WSGIServer):
    """WSGIServer with timeout support."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 1  # 1秒ごとにポーリング可能

def application(environ, start_response):
    method = environ['REQUEST_METHOD']
    path = environ['PATH_INFO']
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, path.lstrip('/'))  # パスの先頭のスラッシュを除去

    if method == 'OPTIONS':
        # CORS対応：プリフライトリクエストへの応答
        start_response('200 OK', [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type'),
        ])
        return [b'']

    if method == 'GET':
        # 静的ファイルの処理
        file_ext = os.path.splitext(file_path)[1]
        mime_type = MIME_TYPES.get(file_ext)

        if mime_type and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as static_file:
                    file_content = static_file.read()

                start_response('200 OK', [
                    ('Access-Control-Allow-Origin', '*'),  # CORS対応
                    ('Content-Type', mime_type),
                    ('Content-Length', str(len(file_content))),
                ])
                return [file_content]

            except Exception as e:
                error_message = f"Error reading file: {e}"
                start_response('500 Internal Server Error', [
                    ('Access-Control-Allow-Origin', '*'),  # CORS対応
                    ('Content-Type', 'text/plain; charset=utf-8'),
                ])
                return [error_message.encode('utf-8')]

        else:
            start_response('404 Not Found', [
                ('Access-Control-Allow-Origin', '*'),  # CORS対応
                ('Content-Type', 'text/plain'),
            ])
            return [b"File not found"]

    if method == 'POST':
        try:
            # POSTデータを取得
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(content_length).decode('utf-8')

            if not body.strip():
                raise ValueError("Received SQL query is empty.")

            # 一時ファイル名を生成
            temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            temp_db_name = temp_db.name
            temp_db.close()

            temp_svg = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
            temp_svg_name = temp_svg.name
            temp_svg.close()

            try:
                # SQLiteデータベースにSQLを実行
                connection = sqlite3.connect(temp_db_name)
                cursor = connection.cursor()
                cursor.executescript(body)
                connection.commit()
                connection.close()

                # ERAlchemyを使ってSVG形式を生成
                render_er(f"sqlite:///{temp_db_name}", temp_svg_name)

                # SVGファイルを返す
                with open(temp_svg_name, "r", encoding="utf-8") as svg_file:
                    svg_data = svg_file.read()

                start_response('200 OK', [
                    ('Access-Control-Allow-Origin', '*'),  # CORS対応
                    ('Content-Type', 'image/svg+xml'),
                    ('Content-Length', str(len(svg_data))),
                ])
                return [svg_data.encode('utf-8')]

            finally:
                # 一時ファイルはcronジョブで削除
                pass

        except Exception as e:
            error_message = f"Error: {e}"
            start_response('500 Internal Server Error', [
                ('Access-Control-Allow-Origin', '*'),  # CORS対応
                ('Content-Type', 'text/plain; charset=utf-8'),
            ])
            return [error_message.encode('utf-8')]

    else:
        start_response('405 Method Not Allowed', [
            ('Access-Control-Allow-Origin', '*'),  # CORS対応
            ('Content-Type', 'text/plain'),
        ])
        return [b"Only POST and GET methods are supported."]

# サーバの起動と停止を管理
def run_server():
    global server
    port = 18080
    server = make_server('', port, application, server_class=TimeoutWSGIServer)
    print(f"Serving on port {port}... (Press Ctrl+C to stop)")

    try:
        while True:
            server.handle_request()  # タイムアウト設定でポーリング
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")

if __name__ == '__main__':
    run_server()
