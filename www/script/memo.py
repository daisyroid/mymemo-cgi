#!/usr/bin/env python3

import cgi
import html
import os
import re
import sqlite3
import sys
import threading
import urllib

# stdoutを確実にutf-8にする
sys.stdout.reconfigure(encoding="utf-8")


# 基本データの取得
def getConstData():
    method = os.environ.get("REQUEST_METHOD", "").upper()
    script_name = os.environ.get("SCRIPT_NAME", "")
    my_name = os.path.basename(script_name)
    my_dir = os.path.dirname(script_name)
    doc_root = os.environ.get("DOCUMENT_ROOT", "../")
    db_file = os.path.abspath(os.path.join(doc_root, "../data/memo.db"))
    return method, my_name, my_dir, db_file


METHOD, MY_NAME, MY_DIR, DB_FILE = getConstData()


# フォームデータの取得
def getFormData():
    form = cgi.FieldStorage()
    query = form.getfirst("q", "").strip()
    delid = form.getfirst("del", "").strip()
    text = form.getfirst("text", "").strip()
    text = "\n".join(text.splitlines())  # 改行コードを"\n"に統一
    return query, delid, text


QUERY, DEL_ID, TEXT = getFormData()


# DBの読み書き
DB_LOCK = threading.Lock()


def getPostData():
    post_data = []
    error_message = ""
    with DB_LOCK:
        try:
            # DB接続（なければ作成）
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at DATETIME DEFAULT (DATETIME('now', 'localtime'))
            )
            """
            cursor.execute(sql)
            conn.commit()

            # 投稿追加または削除
            if TEXT != "":
                sql = "INSERT INTO posts (text) VALUES (?)"
                cursor.execute(sql, (TEXT,))
                conn.commit()
            elif DEL_ID != "":
                sql = "DELETE FROM posts WHERE id = ?"
                cursor.execute(sql, (DEL_ID,))
                conn.commit()

            # ワード検索または全文取得
            if QUERY != "":
                sql = "SELECT * FROM posts WHERE text LIKE ? ORDER BY id DESC"
                cursor.execute(sql, (f"%{QUERY}%",))
                conn.commit()
                post_data = cursor.fetchall()
            else:
                sql = "SELECT * FROM posts ORDER BY id DESC"
                cursor.execute(sql)
                conn.commit()
                post_data = cursor.fetchall()

        except sqlite3.Error as e:
            error_message = f"ERROR: {e}"

        finally:
            conn.close()

    return post_data, error_message


POST_DATA, SYSTEM_MESSAGE = getPostData()


# URLを示す正規表現
URL_PATTERN = re.compile(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+", re.ASCII)


# 文字列をURL部分とそうでない部分に分割する
def split_by_url(text):
    result = []
    last_idx = 0

    # finditerでテキスト内のURLを順番に探す
    for match in re.finditer(URL_PATTERN, text):
        start, end = match.span()

        # URLの前の「地の文」があれば追加
        if start > last_idx:
            result.append((False, text[last_idx:start]))

        # マッチしたURLを追加
        result.append((True, text[start:end]))

        last_idx = end

    # 最後のURLより後ろに文字があれば追加
    if last_idx < len(text):
        result.append((False, text[last_idx:]))

    return result


# すべてのURLをリンク化し、全体をHTMLエスケープする
def linkify_and_escape(text):
    stack = []
    for is_url, text_piece in split_by_url(text):
        if is_url:
            try:
                link_text = urllib.parse.unquote(text_piece)
            except Exception:
                link_text = text_piece
            safe_url = html.escape(text_piece)
            safe_link_text = html.escape(link_text)
            stack.append(
                f'<a href="{safe_url}" target="_blank" rel="noreferrer">{safe_link_text}</a>'
            )
        else:
            safe_text = html.escape(text_piece)
            stack.append(safe_text)
    return "".join(stack)


# POST_DATAからタイムラインのHTMLを作る
def makeTimeLine(data):
    timeline = ""
    for ID, text, created_at in data:
        safe_text = linkify_and_escape(text)
        timeline += (
            f'  <form class="view" method="post" action="{MY_NAME}">\n'
            f'    <div class="header">\n'
            f'      <span class="date">{created_at}</span>\n'
            f'      <input type="hidden" name="del" value="{ID}">\n'
            f'      <button class="del" type="submit">削除</button>\n'
            f'      <button class="copy" type="button">テキストをコピー</button>\n'
            f"    </div>\n"
            f'    <div class="text">{safe_text}</div>\n'
            f"  </form>\n"
        )
    return timeline


TIMELINE = makeTimeLine(POST_DATA)


# 検索ワードの有無で検索ボタンを変える
if QUERY == "":
    CLEAR_BUTTON = ""
    QUERY_BUTTON = '<button type="submit">検索する</button>'
    QUERY_STATUS = ""
else:
    CLEAR_BUTTON = '<button type="button" onclick="location.href=location.pathname;">クリア</button>'
    QUERY_BUTTON = '<button type="submit">検索しなおす</button>'
    QUERY_STATUS = f"  <div>検索結果は{len(POST_DATA)}件です</div>"

# POSTメソッドで、SYSTEM_MESSAGEがない場合はページをリロードする
if METHOD == "POST" and SYSTEM_MESSAGE == "":
    RELOAD_JS = "<script>location.href=location.pathname;</script>"
else:
    RELOAD_JS = ""

# 入力されたデータを表示用にエスケープする
SAFE_QUERY = html.escape(QUERY)
SAFE_TEXT = html.escape(TEXT)

# HTTPレスポンスを出力する
print(
    f"""
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html lang="ja">
<head>{RELOAD_JS}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>なんでもメモ</title>
<link rel="stylesheet" type="text/css" href="../lib/memo-style.css">
<script src="../lib/memo-script.js"></script>
</head>
<body>
<div id="main">
  <h1>なんでもメモ</h1>
  <form class="article" method="post" action="{MY_NAME}">
    <textarea name="text" placeholder="投稿文..." required>{SYSTEM_MESSAGE}</textarea>
    <button type="submit">投稿する</button>
  </form>
  <form class="search" method="get" action="{MY_NAME}">
    <input type="text" name="q" placeholder="検索ワード..." required value="{SAFE_QUERY}">
    {CLEAR_BUTTON}{QUERY_BUTTON}
  </form>
{QUERY_STATUS}
{TIMELINE}
</div>
</body>
</html>
""".strip()
)
