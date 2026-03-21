import http.server

# CGIを使う場合は http.server.CGIHTTPRequestHandler に変更
handler_class = http.server.SimpleHTTPRequestHandler

# サーバーを起動する
host = "localhost"
port = 8000
myserver = http.server.HTTPServer((host, port), handler_class)

print(f"start: http://{host}:{port}")
myserver.serve_forever()
