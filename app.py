from genericpath import isdir
from unittest import result
from flask import render_template, Flask, request, redirect, url_for,session,Blueprint
import base64
from PIL import Image
from io import BytesIO
import os
from PIL import Image
import mediapipe as mp
import numpy as np
import re

# アプリ起動時に骨格画像を保存するフォルダの作成
if not os.path.isdir('./static/image'):
    os.mkdir('./static/image')
    
#骨格推定に必要なインスタンスを生成
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=2,
    enable_segmentation=True,
    min_detection_confidence=0.5)

# 骨格推定の関数を定義
# 出力は各ランドマークの正規化された座標
def pose_est(image):
    results = pose.process(image)
    return results.pose_landmarks


# ----------------------------------------ここからFlask---------------------------------------------
app = Flask(__name__,static_folder='./static')
image = Blueprint("image", __name__, static_url_path='/image', static_folder='./static/image')
app.register_blueprint(image)

#セッションキーの設定
app.config['SECRET_KEY'] = 'teltelpose'

# アプリにアクセスしたらindex.htmlに遷移
# 遊び終わって再度遊びなおす場合遊んだ時の骨格画像を削除
@app.route('/',methods=['POST', 'GET'])
def index():
    img_folder = os.listdir('./static/image')
    for img in img_folder:
        os.remove('./static/image/'+img)

    return render_template('index.html')


# プレイヤー名が送られてきたときの処理
@app.route('/odai',methods=['POST'])
def odai():
    player_list = request.form.getlist('player_name')
    
    # 以前遊んだ時のプレイヤー名残っているときは新しいプレイヤー名に更新
    if 'player_list' in session:
        session['player_list'] = player_list
        session['player_num']  = len(player_list)
        session['count']       = 0
        session['anser_predict'] = []

    # セッションにプレーヤー名が残っていなかったら新規登録
    else:
        session['player_list'] = player_list
        session['player_num']  = len(player_list)
        session['count']       = 0
        session['anser_predict'] = []

    return render_template('odai.html',owner = player_list[session['count']])



# プレイ中の処理
@app.route('/playing',methods=['GET','POST'])
def get_odai():
    # 骨格画像をソートして後ろから4番目を抽出
    user_name = session['player_list'][session['count']]
    images = sorted(os.listdir('./static/image'), key=lambda s: int(re.search(r'\d+', s).group()))
    images = ['image/'+img for img in images[-4:]]

    # プレイヤーが伝言者or出題者の場合
    if session['count']+1 <= len(session['player_list'])-1:
        # 次の人が伝言者の場合
        if session['count']+1 <= len(session['player_list'])-2:
            next_user = session['player_list'][session['count']+1]+'さんに骨格を送る！'
        
        # 次の人が回答者の場合
        elif session['count']+1 == len(session['player_list'])-1:
            next_user = session['player_list'][session['count']+1]+'さんに答えてもらう！'

        # 回答者の回答をセッションに保存
        if request.method=='POST':
            odai = request.form.get('odai')
            if 'odai' in session:
                session['odai'] = odai
            else:
                session['odai'] = odai
            return render_template('play.html',user_name = user_name, next_user = next_user,images=images, len=session['count'])
        
        else:
            return render_template('play.html',user_name = user_name,  next_user = next_user, images=images, len=session['count'])

    else:
        return render_template('anser.html', anser_user=user_name, images=images)
    





#骨格を送るボタンを押したら処理される部分
@app.route('/image_save', methods=['POST','GET'])
def image_save():
    file = './base.jpg'
    base_image = Image.open(file)
    base_image = np.asarray(base_image)
    image_num = ['img1','img2','img3','img4']
    user_num = session['count']
    anser = request.form['anser']

    #伝言者の回答が空白の場合「未回答」に書き直す 
    if anser == '':
        anser='未回答'
    session['anser_predict'].append(anser)

    # ajax通信で送られた各画像データをデコードし骨格検出
    for i,num in enumerate(image_num):
        enc_data  = request.form[num]
        dec_data = base64.b64decode(enc_data.split(',')[1] ) # 環境依存の様(","で区切って本体をdecode)
        # print(dec_data)
        dec_img  = Image.open(BytesIO(dec_data)).convert('RGB')
        dec_img  = np.asarray(dec_img)
        # print(dec_img)
        result = pose_est(dec_img)
        base = base_image.copy()

        # 白い画像に骨格をトレースし画像を保存
        mp_drawing.draw_landmarks(
                base,
                result,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
                connection_drawing_spec=mp_drawing.DrawingSpec())
        im = Image.fromarray(base)
        im.save('./static/image/image'+str(user_num)+str(i)+'.jpg')
    session['count']+=1
    user_name = session['player_list'][session['count']]

    return redirect(url_for('get_odai'))
    

# これまでの伝言者と出題者の骨格と回答をまとめる処理
@app.route('/anser',methods=['GET','POST'])
def anser():
    anser = request.form.get('anser_txt')
    odai = session['odai']
    player_list = session['player_list']
    images = sorted(os.listdir('./static/image'), key=lambda s: int(re.search(r'\d+', s).group()))
    image_list = ['image/'+img for img in images]
    image_list = [image_list[idx:idx + 4] for idx in range(0,len(image_list), 4)]
    
    return render_template('result.html', anser=anser, odai=odai, player_list=player_list, images_list=image_list, predict_list = session['anser_predict'])



if __name__=="__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0')