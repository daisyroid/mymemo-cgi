import os
import functools
import http.server
import socketserver

# ドキュメントルート
DOC_ROOT = os.path.join(os.path.dirname(__file__), "www")

# CGIが実行可能なディレクトリ
CGI_DIR = ["/script"]


# CGIHTTPRequestHandlerを継承してMyCGIHandlerクラスを作る
class MyCGIHandler(http.server.CGIHTTPRequestHandler):
    # CGIディレクトリを設定する：デフォルトは ['/cgi-bin', '/htbin']
    cgi_directories = CGI_DIR

    # CGIディレクトリ内のディレクトリリスト表示を許可する
    # 本来はCGIディレクトリ内が丸見えだと危険なので403エラー
    def is_cgi(self):
        fullpath = self.translate_path(self.path)
        if os.path.isdir(fullpath):
            return False
        else:
            return super().is_cgi()


# HTTPServerとThreadingMixInを継承してThreadedHTTPServerクラスを作る
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    # (host, port)が既に使われていたらエラーにする
    allow_reuse_address = False


# MyCGIHandlerが作られるたびにドキュメントルートを設定する
myhandler = functools.partial(MyCGIHandler, directory=DOC_ROOT)

# 環境変数DOCUMENT_ROOTを設定する
os.environ["DOCUMENT_ROOT"] = DOC_ROOT

# サーバーを起動する
host = "localhost"
port = 8000

try:
    myserver = ThreadedHTTPServer((host, port), myhandler)
    print(f"start: http://{host}:{port}")
    myserver.serve_forever()

except KeyboardInterrupt:
    # [Ctrl]+[C]で中断
    print("\nshutdown...")
    myserver.server_close()

except OSError as e:
    import errno

    if e.errno == errno.EADDRINUSE:
        # アドレス(host, port)が既に使われていた
        print(f"ERROR: {host}:{port} is in use")
    else:
        print(e)
