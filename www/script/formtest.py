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
def getFormData():
    form = cgi.FieldStorage()

    lines = ""
    for key in form.keys():
        val = form.getfirst(key, "")
        lines += f"{key}=[{val}]\n"

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

    password = form.getfirst("password", "")

    return username, password, lines

USERNAME, PASSWORD, LINES = getFormData()

SAFE_USERNAME = html.escape(USERNAME)
SAFE_PASSWORD = html.escape(PASSWORD)
SAFE_LINES    = html.escape(LINES)

# POSTメソッドを処理したあとはページをリロードする
# http.serverは301リダイレクトができないのでJavaScriptを利用
if METHOD == "POST":
    RELOAD_JS = "<script>location.href=location.pathname;</script>"
else:
    RELOAD_JS = ""

RELOAD_JS = ""

# 送信用のHTTPクッキーヘッダを作る
COOKIE_HEADER = COOKIE.output() or ""


# CSSスタイル
STYLE = """
body {
  max-width: 600px;
  margin: 20px auto;
}
.items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}
textarea {
  box-sizing: border-box;
  height: 300px;
}
button {
  padding: 4px 6px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-family: monospace;
  font-size: 12pt;
}
input {
  flex-grow: 1;
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.toggle-password {
  user-select: none; /* テキスト選択を防止 */
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 3px;
}
.password-box {
  display: flex;
  gap: 6px;
  align-items: baseline;
}
"""

SCRIPT = """
  const passwordInput = document.getElementById('password');
  const toggleIcon = document.getElementById('toggleIcon');

  toggleIcon.addEventListener('click', function() {
    // 現在のタイプを確認して切り替える
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      this.textContent = '非表示'; // テキストを書き換え
    } else {
      passwordInput.type = 'password';
      this.textContent = '表示';
    }
  });
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
<body>
  <form method="POST" action="{MY_NAME}" autocomplete="on">
    <div class="items">
      <textarea>{SAFE_LINES}</textarea>
      <input
        type="email"
        id="usermail"
        name="username"
        value="{SAFE_USERNAME}"
        placeholder="username"
      >
      <div class="password-box">
      <input
        type="password"
        id="password"
        name="password"
        value="{PASSWORD}"
        placeholder="password"
      >
      <span id="toggleIcon" class="toggle-password">表示</span>
      </div>
    </div>
    <button type="submit" name="job" value="callme">job:callme</button>
    <button type="submit" name="job" value="logout">job:logout</button>
    <button type="button" onclick="location.href=location.pathname;">reload</button>
  </form>
<script>{SCRIPT}</script>
</body>
</html>
""".strip()
)
