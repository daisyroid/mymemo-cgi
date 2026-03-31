# mymemo-cgi

http.serverとcgiで作った「なんでもメモ」CGIスクリプト

## ファイル構成
* [cgi-server.py](cgi-server.py) -- Webサーバー
* www/
  * script/
    * [memo.py](www/script/memo.py) -- なんでもメモ
    * [memo2.py](www/script/memo2.py) -- なんでもメモv2
  * lib/
    * [memo-style.css](www/lib/memo-style.css) -- スタイルファイル
    * [memo-script.js](www/lib/memo-script.js) -- JavaScriptファイル
* data/
    * ここにSQLiteのデータファイルが作られる

## 使い方

* 配布ファイルは用意していないので [Code] からZIPで落としてください。
* `legacy-cgi`モジュールをインストールしてください。
	```bash
	pip install legacy-cgi
	```
* `cgi-server.py`を起動してください。
	```bash
	python cgi-server.py
	```
* http://localhost:8000/script/memo.py にアクセスしてください。  

## 備考
* `script`フォルダにある`memo.py`以外のファイルはおまけです。<br>
	CGIの実験で作ったものですが、これらを消しても`memo.py`は動作します。
