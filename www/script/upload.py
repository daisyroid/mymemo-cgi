#!/usr/bin/env python3
import cgi
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

UPLOAD_DIR = '../../uploads'
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

try:
    form = cgi.FieldStorage()
    if "file_data" in form:
        file_item = form["file_data"]
        if file_item.filename:
            name = os.path.basename(file_item.filename)
            save_path = os.path.join(UPLOAD_DIR, name)

            # ファイルをバイナリモードで書き込み
            with open(save_path, 'wb') as f:
                f.write(file_item.file.read())
            SYSTEM_MESSAGE = f"成功: {name} を保存しました"
        else:
            SYSTEM_MESSAGE = "エラー: ファイルが選択されていません"
    else:
        SYSTEM_MESSAGE = "ファイルをアップロードしてください"

except Exception as e:
    SYSTEM_MESSAGE = f"{e}"

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