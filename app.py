from genericpath import isdir
from unittest import result
from flask import render_template, Flask, Response, request, redirect, url_for,session,Blueprint
import base64
from PIL import Image
from io import BytesIO
import os
from PIL import Image
import mediapipe as mp
import numpy as np

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

def pose_est(image):
    results = pose.process(image)
    return results.pose_landmarks


# ----------------------------------------ここからFlask---------------------------------------------
app = Flask(__name__,static_folder='./static/image')
image = Blueprint("image", __name__, static_url_path='/image', static_folder='./static/image')
app.register_blueprint(image)

#セッションキーの設定
app.config['SECRET_KEY'] = 'teltelpose'




@app.route('/',methods=['POST', 'GET'])
def index():
    img_folder = os.listdir('./static/image')
    for img in img_folder:
        os.remove('./static/image/'+img)

    return render_template('index.html')



@app.route('/odai',methods=['POST'])
def odai():
    player_list = request.form.getlist('player_name')
    
    if 'player_list' in session:
        session['player_list'] = player_list
        session['player_num']  = len(player_list)
        session['count']       = 0
        session['anser_predict'] = []
    else:
        # pass
        session['player_list'] = player_list
        session['player_num']  = len(player_list)
        session['count']       = 0
        session['anser_predict'] = []

    # print(session['player_list'])
    # print(session['player_num'])
    return render_template('odai.html',owner = player_list[session['count']])




@app.route('/playing',methods=['GET','POST'])
def get_odai():
    user_name = session['player_list'][session['count']]
    images = ['image/'+img for img in os.listdir('./static/image')[-4:]]
    # print(images)
    if session['count']+1 <= len(session['player_list'])-1:
        if session['count']+1 <= len(session['player_list'])-2:
            next_user = session['player_list'][session['count']+1]+'さんに骨格を送る！'
        elif session['count']+1 == len(session['player_list'])-1:
            next_user = session['player_list'][session['count']+1]+'さんに答えてもらう！'

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
    if anser == '':
        anser='未回答'
    session['anser_predict'].append(anser)
    for i,num in enumerate(image_num):
        enc_data  = request.form[num]
        dec_data = base64.b64decode(enc_data.split(',')[1] ) # 環境依存の様(","で区切って本体をdecode)
        # print(dec_data)
        dec_img  = Image.open(BytesIO(dec_data)).convert('RGB')
        dec_img  = np.asarray(dec_img)
        # print(dec_img)
        result = pose_est(dec_img)
        base = base_image.copy()
        mp_drawing.draw_landmarks(
                base,
                result,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        im = Image.fromarray(base)
        im.save('./static/image/image'+str(user_num)+str(i)+'.jpg')
    session['count']+=1
    user_name = session['player_list'][session['count']]
    # print(user_name)
    return redirect(url_for('get_odai'))
    
@app.route('/anser',methods=['GET','POST'])
def anser():
    anser = request.form.get('anser_txt')
    odai = session['odai']
    player_list = session['player_list']
    image_list = ['image/'+img for img in os.listdir('./static/image')]
    image_list = [image_list[idx:idx + 4] for idx in range(0,len(image_list), 4)]
    # print(image_list)
    
    return render_template('result.html', anser=anser, odai=odai, player_list=player_list, images_list=image_list, predict_list = session['anser_predict'])



if __name__=="__main__":
    app.run(debug=True)