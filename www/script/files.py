#!/usr/bin/env python3

import os
import sys
import html

# stdout出力を確実にutf-8にする
sys.stdout.reconfigure(encoding="utf-8")

# ドキュメントルートを得る
doc_root = os.environ.get("DOCUMENT_ROOT") or "."


# ディレクトリdを再帰的にスキャンする
def make_tree(d, maxlevel=10, level=0):
    spaces = " " * (level * 4)
    result = f"{spaces}<ul>\n"
    for name in sorted(os.listdir(d)):
        path = os.path.join(d, name)
        if not os.path.isdir(path):
            url = "/" + os.path.relpath(path, doc_root)
            url = url.replace(os.sep, "/")
            result += f'{spaces}  <li><a href="{url}">{name}</a></li>\n'
        elif level + 1 >= maxlevel:
            result += f"{spaces}  <li>[{name}] ...(略)</li>\n"
        else:
            result += f"{spaces}  <li>[{name}]\n"
            result += make_tree(path, maxlevel, level + 1)
            result += f"{spaces}  </li>\n"
    result += f"{spaces}</ul>\n"
    return result


# ドキュメントルート以下のファイルツリーを得る
tree = make_tree(doc_root, maxlevel=3)

# HTTPレスポンスを出力する
print(f"""Content-Type: text/html

<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ファイルツリー</title>
</head>
<body style="margin: 24px auto; max-width: 600px;">
<h1>ファイルツリー</h1>
{tree.strip()}
</body>
</html>
""")
