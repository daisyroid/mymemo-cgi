#!/usr/bin/env python3

import cgi
import datetime
import html
import os
import re
import sqlite3
import sys
import threading
import urllib

# ////////////////////////// ユーティリティ

# URLを示す正規表現
URL_PATTERN = re.compile(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+", re.ASCII)


# 文字列をURL部分とそうでない部分に分割する
def splitByUrl(text):
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


# テキスト内のURLをすべてリンク化し、全体をHTMLエスケープする
def linkifyAndEscape(text):
    stack = []

    for is_url, text_piece in splitByUrl(text):
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


# "YYYY-MM-DD HH:MM:SS" から "YYYY-MM-DD(曜) HH:MM" を得る
def getDateTimeStr(created_at):
    dt = datetime.datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    wday = ["月", "火", "水", "木", "金", "土", "日"][dt.weekday()]
    return f"{created_at[0:10]}({wday}) {created_at[11:16]}"


# ////////////////////////// 処理開始

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
    try:
        with DB_LOCK:
            with sqlite3.connect(DB_FILE) as conn:
                # DB接続（なければ作成）
                cursor = conn.cursor()
                sql = """
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    created_at DATETIME DEFAULT (DATETIME('now', 'localtime'))
                )
                """
                cursor.execute(sql)

                # 投稿追加または削除
                if TEXT != "":
                    sql = "INSERT INTO posts (text) VALUES (?)"
                    cursor.execute(sql, (TEXT,))
                elif DEL_ID != "":
                    sql = "DELETE FROM posts WHERE id = ?"
                    cursor.execute(sql, (DEL_ID,))
                conn.commit()

                # ワード検索または全文取得
                if QUERY != "":
                    sql = "SELECT * FROM posts WHERE text LIKE ? ORDER BY id DESC"
                    cursor.execute(sql, (f"%{QUERY}%",))
                else:
                    sql = "SELECT * FROM posts ORDER BY id DESC"
                    cursor.execute(sql)
                post_data = cursor.fetchall()

    except sqlite3.Error as e:
        error_message = f"ERROR: {e}"

    return post_data, error_message


POST_DATA, SYSTEM_MESSAGE = getPostData()


# POST_DATAからタイムラインのHTMLを作る
def makeTimeLine(data):
    timeline = ""

    for ID, text, created_at in data:
        safe_text = linkifyAndEscape(text)
        datetime_str = html.escape(getDateTimeStr(created_at))
        timeline += (
            f'  <form class="view" method="post" action="{MY_NAME}">\n'
            f'    <div class="header">\n'
            f'      <span class="date">{datetime_str}</span>\n'
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
def makeQueryBox():
    reload_snippet = "location.href=location.pathname;"

    if QUERY == "":
        c_button = ""
        q_button = '<button type="submit">検索する</button>'
        q_status = ""

    else:
        c_button = f'<button type="button" onclick="{reload_snippet}">クリア</button>'
        q_button = '<button type="submit">検索しなおす</button>'
        q_status = f"  <div>検索結果は{len(POST_DATA)}件です</div>"

    return c_button, q_button, q_status


CLEAR_BUTTON, QUERY_BUTTON, QUERY_STATUS = makeQueryBox()


# POSTメソッドの処理後にページをリロードする仕組み
def makeReloader():
    reload_snippet = "location.href=location.pathname;"

    if METHOD == "GET":
        # GETを処理した場合はリロードする必要なし
        js = ""
        button = ""

    elif SYSTEM_MESSAGE == "":
        # POSTを処理して、ノーエラーの場合、JavaScriptで強制リロード
        js = f"<script>{reload_snippet}</script>"
        button = ""

    else:
        # POSTを処理して、エラーメッセージを出す場合、リロードボタンを付加
        js = ""
        button = f' <button type="button" onclick="{reload_snippet}">リロード</button>'

    return js, button


RELOAD_JS, RELOAD_BUTTON = makeReloader()


# フォームから送信されたデータは表示前にエスケープする
SAFE_QUERY = html.escape(QUERY)

# 出力するページのHTMLを作る
OUTPUT_HTML = f"""
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
    <button type="submit">投稿する</button>{RELOAD_BUTTON}
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


# HTTPレスポンス(ヘッダー,空行,コンテンツ)を出力する
def outputResponse(contents):
    # contentsをバイナリに変換することで、
    # 改行コードの自動変換の影響を排除してバイト数を得る
    bin_contents = contents.encode("utf-8")
    length = len(bin_contents)

    # HTTPヘッダーの改行コードは"\r\n"と定められている
    # WindowsでもLinuxでも"\r\n"にするためバイナリで出力する
    bin_headers = (
        f"Content-Type: text/html; charset=utf-8\r\n"  # Type
        f"Content-Length: {length}\r\n"  # Length
        "\r\n"  # 空行
    ).encode("utf-8")

    # 標準出力にバイナリとして書き込む
    sys.stdout.buffer.write(bin_headers)
    sys.stdout.buffer.write(bin_contents)
    sys.stdout.buffer.flush()


outputResponse(OUTPUT_HTML)
