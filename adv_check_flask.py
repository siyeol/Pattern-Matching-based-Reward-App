from flask import Flask, Response, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import datetime
import pymysql
from kafka import KafkaProducer 

db = pymysql.connect(host="localhost", user="root", passwd="1234", db="free_board", charset="utf8")
cursor = db.cursor()

MIN_MATCH_COUNT = 10

producer=KafkaProducer(acks=0, #메시지 받은 사람이 메시지를 잘 받았는지 체크하는 옵션 (0은 그냥 보내기만 한다. 확인x)
    compression_type='gzip', #메시지 전달할 때 압축
    api_version=(0,11,5),
    bootstrap_servers=['localhost:9092'], #전달하고자하는 카프카 브로커의 위치
    value_serializer=lambda x: dumps(x).encode('utf-8')
)

app = Flask(__name__)
CORS(app)

@app.route('/validate/<adv_name>', methods=['POST'])
@cross_origin()
def adv_check(adv_name):
    lat = request.files['location']['latitude']
    lon = request.files['file']['longitude']

    #*** data가 들어갈 자리에 사용자가 찍은 이미지를 byte로 읽고 JSON에 byteString을 담아서 주면됨!!! ****
    data = request.files['file']
    data_str = data.read()
    #byte 단위 이미지를 cv에 읽히기
    encoded_img = np.fromstring(data_str, dtype = np.uint8)
    img1 = cv.imdecode(encoded_img, 0) # 사용자가 찍은 이미지
    img1 = cv.normalize(img1, None, 0, 255, cv.NORM_MINMAX).astype('uint8') 
    #cv2.CV_LOAD_IMAGE_UNCHANGED                   
    img2 = cv.imread('test.png',0) # 광고 원본

    # Initiate SIFT detector
    sift = cv.SIFT_create()

    # find the keypoints and descriptors with SIFT
    _, des1 = sift.detectAndCompute(img1,None)
    _, des2 = sift.detectAndCompute(img2,None)
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)
    flann = cv.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1,des2,k=2)

    # store all the good matches as per Lowe's ratio test.
    good = []
    total = []
    for m,n in matches:
        total.append(m)
        if m.distance < 0.7*n.distance:
            good.append(m)
    if len(good)/len(total)*100>MIN_MATCH_COUNT: #10% 이상이 일치하면 Kafka Produce
        store_data = {'location':{'latitude':lat,'longitude':lon},'name':adv_name}
        val = jsonify(store_data)
        producer.send('opencv',value=val)
        producer.flush()
        return "True"
    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        return "Not enough matches are found"
        # matchesMask = None


@app.route('/update', methods=['POST'])
@cross_origin()
def update():
    req = request.get_json()
    uid = req["uid"]
    time = str(datetime.datetime.now())

    db=db.connection()
    query_insert = '''
    INSERT INTO user_log (uid, time, point) VALUES(%d, '%s', %d);
    ''' % (uid, time, 2)

    query_update = '''
    UPDATE user_point SET point=point+1 WHERE uid='%s';
    ''' % (uid)
    
    cursor.execute(query_insert)
    cursor.execute(query_update)
    
    db.commit()

    return "Update Success"
    

@app.route('/mypage', methods=['POST'])
@cross_origin()
def fetch_mypage():
    req = request.get_json()
    uid = req["uid"]

    db=db.connection()
    query_select = '''
    SELECT uid, COUNT(point) FROM user_log WHERE uid = "%s" GROUP BY uid;
    ''' % (uid)
    
    cursor.execute(query_select)
    
    result = cursor.fetchall()

    return result
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)