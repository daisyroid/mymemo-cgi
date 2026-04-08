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


# テキスト内のURLをすべてリンク化し、全体をHTMLエスケープする
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


# "YYYY-MM-DD HH:MM:SS" から "YYYY-MM-DD(曜) HH:MM" を得る
def get_datetime_str(created_at):
    dt = datetime.datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    wday = ["月", "火", "水", "木", "金", "土", "日"][dt.weekday()]
    return f"{created_at[0:10]}({wday}) {created_at[11:16]}"


# 文字列sを整数化する
def get_int(s, default=0):
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


# ////////////////////////// 処理開始

# stdoutを確実にutf-8にする
sys.stdout.reconfigure(encoding="utf-8")


# 基本データの取得
def get_const_data():
    method = os.environ.get("REQUEST_METHOD", "").upper()
    script_name = os.environ.get("SCRIPT_NAME", "")
    my_name = os.path.basename(script_name)
    my_dir = os.path.dirname(script_name)
    doc_root = os.environ.get("DOCUMENT_ROOT", "../")
    db_file = os.path.abspath(os.path.join(doc_root, "../data/memo.db"))
    return method, my_name, my_dir, db_file


METHOD, MY_NAME, MY_DIR, DB_FILE = get_const_data()


# ページサイズのデフォルト値
DEFAULT_LIMIT = 10


# フォームデータの取得
def get_form_data():
    form = cgi.FieldStorage()
    query = form.getfirst("q", "").strip()
    del_id = form.getfirst("del", "").strip()
    del_id = get_int(del_id, 0)
    text = form.getfirst("text", "").strip()
    text = "\n".join(text.splitlines())  # 改行コードを"\n"に統一

    # a=id: [指定したidの次を表示]
    after = form.getfirst("a", "").strip()
    after = get_int(after, 0)

    # b=id: [指定したidの前を表示]、引数aがあれば引数bは無視する
    if after != 0:
        before = 0
    else:
        before = form.getfirst("b", "").strip()
        before = get_int(before, 0)

    # n=1以上の整数: ページサイズの指定
    limit = form.getfirst("n", "").strip()
    limit = max(1, get_int(limit, DEFAULT_LIMIT))

    return query, del_id, text, after, before, limit


QUERY, DEL_ID, TEXT, AFTER, BEFORE, LIMIT = get_form_data()

# QUERYをサニタイズ（無害化）しておく
SAFE_QUERY = html.escape(QUERY)


# DBの読み書き
DB_LOCK = threading.Lock()


def get_post_data():
    data = []
    more_b = 0
    mora_a = 0
    error_message = ""
    try:
        with DB_LOCK:
            with sqlite3.connect(DB_FILE) as conn:
                # DB接続（なければ作成）
                cursor = conn.cursor()
                sql = (
                    "CREATE TABLE IF NOT EXISTS posts ("
                    "    id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "    text TEXT NOT NULL,"
                    "    created_at DATETIME DEFAULT (DATETIME('now', 'localtime'))"
                    ")"
                )
                cursor.execute(sql)

                # 投稿追加または削除
                if TEXT != "":
                    sql = "INSERT INTO posts (text) VALUES (?)"
                    cursor.execute(sql, (TEXT,))
                elif DEL_ID != 0:
                    sql = "DELETE FROM posts WHERE id = ?"
                    cursor.execute(sql, (DEL_ID,))
                conn.commit()

                # データ取得の共通処理、[戻る][進む]の有効性もチェック
                def fetchAndCheck():
                    # 直前にSQLでSELECTした結果を取得する
                    # その際データ数上限として(LIMIT+1)個を指定している
                    data = cursor.fetchall()

                    # 次のデータがあるかチェックする
                    if len(data) > LIMIT:
                        del data[-1]  # 取りすぎた1個を削除
                        more = True  # 次のデータがある
                    else:
                        more = False  # 次のデータはない

                    # 状況によって分岐する
                    if len(data) == 0:
                        # データが1つも取得できなかった
                        # (原因1) そもそもデータが1つもない
                        # (原因2) aやbに有効範囲外が指定された
                        more_b = False  # [戻る]は無効
                        more_a = False  # [進む]は無効

                    elif AFTER != 0:
                        # [進む]を実行した
                        more_b = True  # 必ず[戻る]が有効
                        more_a = more  # 次のデータがあれば[進む]が有効

                    elif BEFORE != 0:
                        # [戻る]を実行した
                        more_b = more  # 前のデータがあれば[戻る]が有効
                        more_a = True  # 必ず[進む]が有効
                        data.reverse()  # ★重要★ データが逆順なので反転する

                    else:
                        # 最初のページを取得した
                        more_b = False  # [戻る]は無効
                        more_a = more  # 次のデータがあれば[進む]が有効

                    return data, more_b, more_a

                # データを取得する
                if QUERY != "":
                    # 検索あり
                    if AFTER != 0:
                        # 検索あり+[進む]
                        sql = (
                            "SELECT * FROM posts"
                            "   WHERE (text LIKE ?) AND (id < ?)"
                            "   ORDER BY id DESC"
                            "   LIMIT ?"
                        )
                        cursor.execute(sql, (f"%{QUERY}%", AFTER, LIMIT + 1))
                        data, more_b, more_a = fetchAndCheck()

                    elif BEFORE != 0:
                        # 検索あり+[戻る]
                        sql = (
                            "SELECT * FROM posts"
                            "   WHERE (text LIKE ?) AND (id > ?)"
                            "   ORDER BY id ASC"
                            "   LIMIT ?"
                        )
                        cursor.execute(sql, (f"%{QUERY}%", BEFORE, LIMIT + 1))
                        data, more_b, more_a = fetchAndCheck()

                    else:
                        # 検索あり、最初のページ
                        sql = (
                            "SELECT * FROM posts"
                            "   WHERE text LIKE ?"
                            "   ORDER BY id DESC"
                            "   LIMIT ?"
                        )
                        cursor.execute(sql, (f"%{QUERY}%", LIMIT + 1))
                        data, more_b, more_a = fetchAndCheck()

                else:
                    # 検索なし
                    if AFTER != 0:
                        # 検索なし+[進む]
                        sql = (
                            "SELECT * FROM posts"
                            "   WHERE id < ?"
                            "   ORDER BY id DESC"
                            "   LIMIT ?"
                        )
                        cursor.execute(sql, (AFTER, LIMIT + 1))
                        data, more_b, more_a = fetchAndCheck()

                    elif BEFORE != 0:
                        # 検索なし+[戻る]
                        sql = (
                            "SELECT * FROM posts"
                            "   WHERE id > ?"
                            "   ORDER BY id ASC"
                            "   LIMIT ?"
                        )
                        cursor.execute(sql, (BEFORE, LIMIT + 1))
                        data, more_b, more_a = fetchAndCheck()

                    else:
                        # 検索なし、最初のページ
                        sql = "SELECT * FROM posts   ORDER BY id DESC   LIMIT ?"
                        cursor.execute(sql, (LIMIT + 1,))
                        data, more_b, more_a = fetchAndCheck()

    except sqlite3.Error as e:
        error_message = f"ERROR: {e}"

    return data, more_b, more_a, error_message


POST_DATA, MORE_BEFORE, MORE_AFTER, SYSTEM_MESSAGE = get_post_data()


# POST_DATAからタイムラインのHTMLを作る
def make_timeline(data):
    timeline = ""

    for ID, text, created_at in data:
        safe_text = linkify_and_escape(text)
        datetime_str = html.escape(get_datetime_str(created_at))
        timeline += (
            f'  <form class="view" method="post" action="{MY_NAME}">\n'
            f'    <div class="header">\n'
            f'      <span class="date">{datetime_str}</span>\n'
            f'      <input type="hidden" name="del" value="{ID}">\n'
            f'      <button class="del" type="submit">削除:{ID}</button>\n'
            f'      <button class="copy" type="button">テキストをコピー</button>\n'
            f"    </div>\n"
            f'    <div class="text">{safe_text}</div>\n'
            f"  </form>\n"
        )

    return timeline


TIMELINE = make_timeline(POST_DATA)


# 検索ワードの有無で検索ボタンを変える
def make_query_box():
    reload_snippet = "location.href=location.pathname;"

    if QUERY == "":
        c_button = ""
        q_button = '<button type="submit">検索する</button>'
        q_status = ""

    else:
        c_button = f'<button type="button" onclick="{reload_snippet}">クリア</button>'
        q_button = '<button type="submit">検索しなおす</button>'
        has_more = " （まだ先があります）" if MORE_AFTER != 0 else ""
        q_status = f"  <div>検索結果は{len(POST_DATA)}件です{has_more}。</div>"

    return c_button, q_button, q_status


CLEAR_BUTTON, QUERY_BUTTON, QUERY_STATUS = make_query_box()


# ページサイズの選択肢の作成
def make_pagesize_select():
    lines = ['<select class="pagesize" onchange="setPageSize(this.value);">']
    for n in [1, 2, 3, 5, 10, 20, 30, 50, 100]:
        selected = " selected" if n == LIMIT else ""
        lines.append(f'<option value="{n}"{selected}>PageSize={n}</option>')
    lines.append("</select>")
    return "\n".join(lines)


PAGESIZE_SELECT = make_pagesize_select()


# [戻る][進む]リンクの表示
def make_navi_box():
    plist = []

    if QUERY != "":
        plist.append(f"q={SAFE_QUERY}")
    if LIMIT != DEFAULT_LIMIT:
        plist.append(f"n={LIMIT}")

    if MORE_BEFORE:
        min_id = POST_DATA[0][0]
        params = "&".join(plist + [f"b={min_id}"])
        b_link = f'<a href="{MY_NAME}?{params}">[戻る]</a>'
    else:
        b_link = "<s>[戻る]</s>"

    if MORE_AFTER:
        max_id = POST_DATA[-1][0]
        params = "&".join(plist + [f"a={max_id}"])
        a_link = f'<a href="{MY_NAME}?{params}">[進む]</a>'
    else:
        a_link = "<s>[進む]</s>"

    if len(plist) > 0:
        params = "?" + "&".join(plist)
    else:
        params = ""
    reset_link = f'<a href="{MY_NAME}{params}">[最初から]</a>'

    return f'<div class="navi">\n{b_link}\n{reset_link}\n{a_link}\n</div>\n'


NAVI_BOX = make_navi_box()


# POSTメソッドの処理後にページをリロードする仕組み
def make_reloader():
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


RELOAD_JS, RELOAD_BUTTON = make_reloader()

# 出力するページのHTMLを作る
OUTPUT_HTML = f"""
<!DOCTYPE html>
<html lang="ja">
<head>{RELOAD_JS}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>なんでもメモv3</title>
<link rel="stylesheet" type="text/css" href="../lib/memo-style.css">
<script src="../lib/memo-script.js"></script>
</head>
<body>
<div id="main">
  <h1>なんでもメモv3</h1>
  <form class="article" method="post" action="{MY_NAME}">
    <textarea name="text" placeholder="投稿文..." required>{SYSTEM_MESSAGE}</textarea>
    <div class="panel">
      <button type="submit">投稿する</button>{RELOAD_BUTTON}{PAGESIZE_SELECT}
    </div>
  </form>
  <form class="search" method="get" action="{MY_NAME}">
    <input type="text" name="q" placeholder="検索ワード..." required value="{SAFE_QUERY}">
    {CLEAR_BUTTON}{QUERY_BUTTON}
  </form>
{QUERY_STATUS}
{TIMELINE}
{NAVI_BOX}
</div>
</body>
</html>
""".strip()


# HTTPレスポンス(ヘッダー,空行,コンテンツ)を出力する
def output_response(contents):
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


output_response(OUTPUT_HTML)
