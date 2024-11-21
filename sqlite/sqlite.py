import sqlite3
from eralchemy import render_er

# SQLスクリプト
sql_script = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    author_id INTEGER,
    FOREIGN KEY (author_id) REFERENCES users(id)
);
"""

# SQLiteのメモリデータベースを作成
connection = sqlite3.connect(":memory:")
cursor = connection.cursor()

# SQLスクリプトを実行してスキーマを作成
cursor.executescript(sql_script)
connection.commit()

# メモリ上のSQLiteデータベースをファイルに保存
database_file = "example.db"
with sqlite3.connect(database_file) as file_db:
    connection.backup(file_db)

# ERAlchemyを使用してER図を生成
# ファイル名のベース
output_base = "example"

# DOT形式の生成
render_er(f"sqlite:///{database_file}", f"{output_base}.dot")
print(f"Generated: {output_base}.dot")

# SVG形式の生成
render_er(f"sqlite:///{database_file}", f"{output_base}.svg")
print(f"Generated: {output_base}.svg")

# PNG形式の生成
render_er(f"sqlite:///{database_file}", f"{output_base}.png")
print(f"Generated: {output_base}.png")
