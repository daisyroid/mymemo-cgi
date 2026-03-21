# mymemo-cgi

Pythonのhttp.serverとcgiで作る備忘メモ

## ファイル構成
* [web-server.py](web-srver.py) -- 基本的なWebサーバー (sample)
* [cgi-server.py](cgi-srver.py) -- CGIが使えるWebサーバー
* www/
  * [frontpage.html](www/frontpage.html)  -- HTMLファイルの例 (sample)
  * script/
    * [hello.py](www/script/hello.py) -- Hello world! (sample)
    * [envs.py](www/script/envs.py) -- 環境変数を表示 (sample)
    * [files.py](www/script/files.py) -- www以下のファイルをツリー表示 (sample)
    * [welcome.py](www/script/welcome.py) -- cgiとhttp.cookiesの利用例 (sample)
    * [memo.py](www/script/memo.py) -- SQLiteを利用した備忘メモ
  * lib/
    * [memo-style.css](www/lib/memo-style.css)
    * [memo-script.js](www/lib/memo-script.js)
* data/

## 使い方
1. `pip install legacy-cgi`
2. `python cgi-server.py`
3. ブラウザで http://localhost:8000/ を開く

* www/script/memo.py が備忘メモ本体です。<br>
    www/lib/memo-style.css と www/lib/memo-script.js を利用します。

* 上のファイル構成で(sample)とあるのは実験で作ったファイルです。<br>
    これらを消してもmemo.pyは動作します。
# mymemo-cgi
