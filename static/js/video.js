function send_img(ctx){
  //canvas elementを取得
  // var canvas = document.getElementById('canvas');
  //base64データを取得（エンコード）
  var base64 = ctx.toDataURL('image/png');
  // console.log(base64)
  var fData = new FormData();
  fData.append('img', base64);
  console.log(fData.get('img'))

// ajax送信
  $.ajax({
      //画像処理サーバーに返す場合
      url: "/image_save",   
      type: 'POST',
      data: fData ,
      contentType: false,
      processData: false,
      success: function(data, dataType) {
          //非同期で通信成功時に読み出される [200 OK 時]
          console.log('Success', data);
      },
      error: function(XMLHttpRequest, textStatus, errorThrown) {
          //非同期で通信失敗時に読み出される
          console.log('Error : ' + errorThrown);
      }
  });
}

// windowが読み込まれたタイミングで行う処理
window.onload = () => {
  // HTML側のオブジェクトを指定
const video  = document.querySelector("#camera");
const canvas = document.querySelector("#picture");
const se     = document.querySelector('#se');
const aa     = document.querySelector('#img_a');

/** カメラ設定 */
//   音は無し
// 大きさ200×300
// インカメラに指定
const constraints = {
  audio: false,
  video: {
    height: 200,
    width: 300,
    facingMode: "user"   // フロントカメラを利用する
    // facingMode: { exact: "environment" }  // リアカメラを利用する場合
  }
};

/**
 * カメラを<video>と同期
 */
navigator.mediaDevices.getUserMedia(constraints)
.then( (stream) => {
  video.srcObject = stream;
  video.onloadedmetadata = (e) => {
    video.play();
  };
})
.catch( (err) => {
  console.log(err.name + ": " + err.message);
});

/**
 * シャッターボタン
 */
//   シャッターボタンが押されたときの処理
 document.querySelector("#shutter").addEventListener("click", () => {
  const ctx = canvas.getContext("2d");

  // 演出的な目的で一度映像を止めてSEを再生する
  video.pause();  // 映像を停止
  se.play();      // シャッター音
  setTimeout( () => {
    video.play();    // 0.5秒後にカメラ再開
  }, 500);

  // canvasに画像を貼り付ける
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
  send_img(canvas)
});
};

aaa


