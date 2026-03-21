#!/usr/bin/env python3

import cgi
import html
import http.cookies
import os
import sys
import urllib

# stdout出力を確実にutf-8にする
sys.stdout.reconfigure(encoding="utf-8")


# 基本データの取得
def getConstData():
    method = os.environ.get("REQUEST_METHOD", "").upper()
    script_name = os.environ.get("SCRIPT_NAME", "")
    my_name = os.path.basename(script_name)
    my_dir = os.path.dirname(script_name)
    return method, my_name, my_dir

METHOD, MY_NAME, MY_DIR = getConstData()


# クッキー読み書きの準備
COOKIE_DAYS = 30
COOKIE = http.cookies.SimpleCookie()
COOKIE.load(os.environ.get("HTTP_COOKIE", ""))

def get_cookie(key):
    if key in COOKIE:
        return urllib.parse.unquote(COOKIE[key].value)
    else:
        return ""

def set_cookie(key, val, days=COOKIE_DAYS):
    COOKIE[key] = urllib.parse.quote(val)
    COOKIE[key]["path"] = MY_DIR
    COOKIE[key]["domain"] = "localhost"  # CGIサーバーと同じにする
    COOKIE[key]["max-age"] = 3600 * days
    COOKIE[key]["httponly"] = True
    COOKIE[key]["secure"] = False  # localhostなのでSSLなしを許可
    COOKIE[key]["samesite"] = "Lax"

def del_cookie(key):
    set_cookie(key, "", days=-1)


# フォームデータの取得
def getUserName():
    form = cgi.FieldStorage()
    job = form.getfirst("job", "")
    if job == "callme":
        # 名前の設定
        username = form.getfirst("username", "").strip()
        set_cookie("username", username)
    elif job == "logout":
        # ログアウト
        username = ""
        del_cookie("username")
    else:
        # 上記以外の通常アクセス
        username = get_cookie("username")
        # クッキーがあれば有効期間を更新
        if username != "":
            set_cookie("username", username)
    return username

USERNAME = getUserName()
SAFE_USERNAME = html.escape(USERNAME)


# ユーザー名の有無で表示内容を変える
if USERNAME != "":
    BODY_DATA = f"""
  <p>ようこそ <span class="big">{SAFE_USERNAME}</span> さん！</p>
  <p>ブラウザを閉じても、{COOKIE_DAYS}日間は名前を覚えています</p>
  <p>名前を変更したい場合は再入力してください</p>
  <p>名前を消去したい場合はログアウトしてください</p>
  <form method="POST" action="{MY_NAME}">
    <input
      type="text"
      name="username"
      value="{SAFE_USERNAME}"
      placeholder="ここにお名前をどうぞ..."
      required>
    <button type="submit" name="job" value="callme">名前を変更する</button>
    <button type="submit" name="job" value="logout">ログアウトする</button>
  </form>
"""
else:
    BODY_DATA = f"""
  <p><span class="big">初めまして！</span></p>
  <p>お名前を教えてください</p>
  <form method="POST" action="{MY_NAME}">
    <input
      type="text"
      name="username"
      placeholder="ここにお名前をどうぞ..."
      required>
    <button type="submit" name="job" value="callme">名前を教える</button>
  </form>
"""


# POSTメソッドを処理したあとはページをリロードする
# http.serverは301リダイレクトができないのでJavaScriptを利用
if METHOD == "POST":
    RELOAD_JS = "<script>location.href=location.pathname;</script>"
else:
    RELOAD_JS = ""


# 送信用のHTTPクッキーヘッダを作る
COOKIE_HEADER = COOKIE.output() or ""


# CSSスタイル
STYLE = """
body {
  max-width: 600px;
  margin: 20px auto;
}
form {
  display: flex;
  gap: 6px;
}
button {
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
input {
  flex-grow: 1;
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.big {
  font-size: 133%;
  font-weight: bold;
}
"""


# HTTPレスポンスを出力する
print(
    f"""
{COOKIE_HEADER}
Content-Type: text/html; charset=utf-8

<!DOCTYPE html>
<html lang="ja">
<head>{RELOAD_JS}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Welcome</title>
<style>{STYLE}</style>
</head>
<body>{BODY_DATA}</body>
</html>
""".strip()
)
