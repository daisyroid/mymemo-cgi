// [コピー]ボタンを押したときの処理
function onClick(ev) {
  const div = ev.target.parentElement.parentElement.children[1];
  navigator.clipboard.writeText(div.innerText)
    .then(() => {
      // メッセージボックスを作る
      const msgbox = document.createElement('div');
      msgbox.className = 'toast-msgbox';
      msgbox.textContent = 'コピーしました！';
      msgbox.style.left = `${ev.pageX - 120}px`;
      msgbox.style.top = `${ev.pageY - 60}px`;
      // 表示して、0.8秒後に透明化開始、その0.2秒後に消滅
      document.body.appendChild(msgbox);
      setTimeout(() => {
        msgbox.style.opacity = '0';
        setTimeout(() => msgbox.remove(), 200);
      }, 800);
    })
    .catch(err => alert(`コピー失敗: {err}`));
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
  // submitする場合はボタンを無効化（2度押し防止)
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
