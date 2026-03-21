#!/usr/bin/env python3

import os
import sys
import html
import cgi

# stdout出力を確実にutf-8にする
sys.stdout.reconfigure(encoding="utf-8")

# 環境変数の一覧を得る
lines = []
for key, val in sorted(os.environ.items()):
    safe_key = html.escape(key, quote=False)
    safe_val = html.escape(val, quote=False)
    lines.append(f"<tr><td>{safe_key}</td><td>{safe_val}</td></tr>")

# CSSスタイル
style = """
body {
  margin: 24px auto;
  max-width: 600px;
}
table {
  border-collapse: collapse;
  line-height: 120%;
}
th {
  background: #eee;
  border: 1px solid gray;
  padding: 2px 4px;
  text-align: left;
}
td {
  background: #fff;
  border: 1px solid gray;
  padding: 2px 4px;
  overflow-wrap: break-word;
}
.key-val td:nth-of-type(1) {
  font-size: 9pt;
}
.key-val td:nth-of-type(2) {
  font-size: 11pt;
  font-family: monospace;
  word-break: break-all;
}
"""

# HTTPレスポンスを出力する
print(f"""Content-Type: text/html

<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>環境変数</title>
<style>{style}</style>
</head>
<body>
<h1>環境変数</h1>
<table class="key-val">
<tr><th>名前</th><th>値</th></tr>
{"\n".join(lines)}
</table>
</body>
</html>
""")
