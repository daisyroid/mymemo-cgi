#import sys
#sys.stdout.reconfigure(encoding="utf-8")

import http.cookies

# 1. SimpleCookieオブジェクトの作成
c = http.cookies.SimpleCookie()

# 2. セッションクッキーの設定（有効期限を指定しない）
c["session_id"] = "abc123456789"
c["user_mode"] = "dark"

# 3. セキュリティ属性の付与（推奨）
# HttpOnly: JSからのアクセス不可
# Secure: HTTPSのみ
# SameSite: CSRF対策
c["session_id"]["httponly"] = True
c["session_id"]["secure"] = True
c["session_id"]["samesite"] = "Lax"

c["session_id"]["expires"] = 3600

# 4. HTTPヘッダー形式で出力
print(c.output())
'''
print(f"""
Content-Type: text/html; charset=utf-8\n")

<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>CGIファイルアップロード</title>
</head>
<body>
    <p>{SYSTEM_MESSAGE}</p>
    <form action="upload.py" method="post" enctype="multipart/form-data">
        <input type="file" name="file_data">
        <input type="submit" value="アップロード開始">
    </form>
</body>
</html>
""".strip()
)
'''
