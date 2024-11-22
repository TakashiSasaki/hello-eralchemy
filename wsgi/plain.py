# Script file name: plain.py

import sqlite3
import tempfile
import os, signal, sys
from wsgiref.simple_server import make_server
from eralchemy import render_er
from threading import Thread
from time import sleep

# MIMEタイプを拡張子に基づいて設定
MIME_TYPES = {
    '.sql': 'text/plain',
    '.txt': 'text/plain',
    '.plain': 'text/plain',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
}

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

            temp_plain = tempfile.NamedTemporaryFile(suffix=".plain", delete=False)
            temp_plain_name = temp_plain.name
            temp_plain.close()

            try:
                # SQLiteデータベースにSQLを実行
                connection = sqlite3.connect(temp_db_name)
                cursor = connection.cursor()
                cursor.executescript(body)
                connection.commit()
                connection.close()

                # ERAlchemyを使ってPlain形式を生成
                render_er(f"sqlite:///{temp_db_name}", temp_plain_name)

                # plainファイルを返す
                with open(temp_plain_name, "rb") as plain_file:
                    plain_data = plain_file.read()

                start_response('200 OK', [
                    ('Access-Control-Allow-Origin', '*'),  # CORS対応
                    ('Content-Type', 'text/plain'),
                    ('Content-Length', str(len(plain_data))),
                ])
                return [plain_data]

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

# WSGIサーバを別スレッドで起動
def run_server():
    global server
    port = 18080
    server = make_server('', port, application)
    print(f"Serving on port {port}... (Press Ctrl+C to stop)")
    server.serve_forever()

if __name__ == '__main__':
    server_thread = Thread(target=run_server)
    server_thread.start()

    def signal_handler(sig, frame):
        print("\nShutting down server gracefully...")
        server.shutdown()
        server_thread.join()  # スレッドの終了を待つ
        print("Server stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # 無限ループでシグナルを待機
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass
