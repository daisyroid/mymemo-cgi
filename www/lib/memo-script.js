// [コピー]ボタンを押したときの処理
function onClick(ev) {
  // ボタンの親フォームに属するdiv.textが記事本体
  const div = ev.target.form.querySelector("div.text");

  // HTMLを取得し、自動リンクとHTMLエスケープを解除
  const r2c = {
    '&lt;'  : '<',
    '&gt;'  : '>',
    '&amp;' : '&',
    '&quot;': '"',
  };
  const raw_text = div.innerHTML
    .replace(/<a href="([^"]*)"[^>]*>.*?<\/a>/g, '$1')
    .replace(/&(lt|gt|amp|quot);/g, (m) => r2c[m]);

  // クリップボードにコピーする
  navigator.clipboard.writeText(raw_text)
    .then(() => {
      // 成功した場合

      // メッセージボックスを作る
      const msgbox = document.createElement('div');
      msgbox.className = 'toast-message';
      msgbox.textContent = 'コピーしました！';
      msgbox.style.left = `${ev.pageX - 100}px`;
      msgbox.style.top = `${ev.pageY - 60}px`;

      // 表示し、0.7秒後に透明化、その0.3秒後に消滅
      document.body.appendChild(msgbox);
      setTimeout(() => {
        msgbox.style.opacity = '0';
        setTimeout(() => msgbox.remove(), 300);
      }, 700);
    })
    .catch(err => {
      // 失敗した場合
      alert(`コピー失敗: {err}`);
    });
}

// フォームのsubmitイベントの処理
function onSubmit(ev) {
  if (ev.target.className == "view") {
    // viewクラスのsubmitは削除ボタンなので確認する
    if (!confirm("本当に削除しますか")) {
      // キャンセルされたらsubmitせず戻る
      ev.preventDefault();
      return;
    }
  }
  // submitする前にボタンを無効化（2度押し防止)
  for (const btn of document.querySelectorAll("button")) {
    btn.disabled = true;
  }
}

// 初期化時の処理
window.addEventListener("DOMContentLoaded", () => {
  // 全フォームにsubmitイベント処理を追加する
  for (const f of document.querySelectorAll("form")) {
    f.addEventListener("submit", onSubmit);
  }
  // 全コピーボタンにclickイベント処理を追加する
  for (const b of document.querySelectorAll("button.copy")) {
    b.addEventListener("click", onClick);
  }
});
