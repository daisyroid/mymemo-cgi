# mymemo-cgi

Pythonのhttp.serverとcgiで作る備忘メモ

## ファイル構成
* [cgi-server.py](cgi-srver.py) -- CGIが使えるWebサーバー
* www/
  * script/
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

* 上記の4ファイル以外はおまけです。<br>
	CGIの実験で作ったものですが、これらを消してもmemo.pyは動作します。
