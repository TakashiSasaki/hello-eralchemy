import sqlite3
import tempfile
import os
from wsgiref.simple_server import make_server
from eralchemy import render_er

def application(environ, start_response):
    method = environ['REQUEST_METHOD']

    if method == 'OPTIONS':
        # CORS対応：プリフライトリクエストへの応答
        start_response('200 OK', [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type'),
        ])
        return [b'']

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

            temp_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temp_png_name = temp_png.name
            temp_png.close()

            try:
                # SQLiteデータベースにSQLを実行
                connection = sqlite3.connect(temp_db_name)
                cursor = connection.cursor()
                cursor.executescript(body)
                connection.commit()
                connection.close()

                # ERAlchemyを使ってPNGを生成
                render_er(f"sqlite:///{temp_db_name}", temp_png_name)

                # PNGファイルを返す
                with open(temp_png_name, "rb") as png_file:
                    png_data = png_file.read()

                start_response('200 OK', [
                    ('Access-Control-Allow-Origin', '*'),  # CORS対応
                    ('Content-Type', 'image/png'),
                    ('Content-Length', str(len(png_data))),
                ])
                return [png_data]

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
        return [b"Only POST method is supported."]

# WSGIサーバを起動
if __name__ == '__main__':
    port = 18080
    print(f"Serving on port {port}...")
    with make_server('', port, application) as server:
        server.serve_forever()
