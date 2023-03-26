from flask import Flask, Response, request, jsonify, make_response
from flask_cors import CORS, cross_origin
from kafka import KafkaProducer, KafkaConsumer
import pymysql
from pymongo import MongoClient
from elasticsearch import Elasticsearch

import numpy as np
from json import dumps, loads
import os
from threading import Thread
from dotenv import load_dotenv
import cv2 as cv
# from matplotlib import pyplot as plt
from datetime import datetime

from resource_log import ResourceLogger


MIN_MATCH_COUNT = 10

app = Flask(__name__)
CORS(app)

producer=KafkaProducer(acks=0, #메시지 받은 사람이 메시지를 잘 받았는지 체크하는 옵션 (0은 그냥 보내기만 한다. 확인x)
    compression_type='gzip', #메시지 전달할 때 압축
    api_version=(0,11,5),
    bootstrap_servers=['localhost:9092'], #전달하고자하는 카프카 브로커의 위치
    value_serializer=lambda x: dumps(x).encode('utf-8')
)

client = MongoClient('localhost:27017')
collection = client.cash_hunter.match_log

load_dotenv()

db_config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'passwd': os.environ.get('DB_PASSWORD'),
    'db': os.environ.get('DB_NAME'),
    'charset': os.environ.get('DB_CHARSET')
}

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
        store_data = {'success':True,'location':{'latitude':lat,'longitude':lon},'name':adv_name}
        val = jsonify(store_data)
        producer.send('opencv',value=val)
        producer.flush()
        return "True"
    else:
        store_data = {'success':False,'location':{'latitude':lat,'longitude':lon},'name':adv_name}
        val = jsonify(store_data)
        producer.send('opencv',value=val)
        producer.flush()
        return "Not enough matches are found"
        # matchesMask = None


@app.route('/dbsave/mongo', methods=['GET'])
@cross_origin()
def save_mongo():
    consumer = KafkaConsumer(
        'opencv',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=None,
        value_deserializer=lambda x: loads(x.decode('utf-8'))
    )

    for message in consumer:
        record = message.value
        record['timestamp'] = datetime.utcnow()
        collection.insert_one(record)

    return "Kafka Q saved to mongo"


#MySQL

def get_db_connection():
    return pymysql.connect(**db_config)

@app.route('/update', methods=['POST'])
@cross_origin()
def update():
    req = request.get_json()
    uid = req["uid"]
    time = str(datetime.datetime.now())

    connection = get_db_connection()
    cursor = connection.cursor()

    query_insert = '''
    INSERT INTO user_log (uid, time, point) VALUES(%s, %s, %s);
    '''

    query_update = '''
    UPDATE user_point SET point=point+1 WHERE uid=%s;
    '''

    try:
        cursor.execute(query_insert, (uid, time, 2))
        cursor.execute(query_update, (uid,))
        connection.commit()
    except Exception as e:
        connection.rollback()
        return str(e), 500
    finally:
        cursor.close()
        connection.close()

    return "Update Success"
    

@app.route('/mypage', methods=['POST'])
def fetch_mypage():
    req = request.get_json()
    uid = req["uid"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query_select = '''
    SELECT uid, COUNT(point) FROM user_log WHERE uid = %s GROUP BY uid;
    '''

    try:
        cursor.execute(query_select, (uid,))
        result = cursor.fetchall()
    except Exception as e:
        return str(e), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify(result)
    

# Elasticsearch function
def save_to_elasticsearch(es, index, body):
    es.index(index=index, body=body)


# Kafka Consumer function
def consume_and_save_to_elasticsearch(kafka_bootstrap_servers, elasticsearch_hosts):
    es = Elasticsearch(hosts=elasticsearch_hosts)

    consumer = KafkaConsumer(
        'system-metrics',
        bootstrap_servers=kafka_bootstrap_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group',
        value_deserializer=lambda x: loads(x.decode('utf-8'))
    )

    for message in consumer:
        log_record = message.value
        save_to_elasticsearch(es, 'system-metrics', log_record)


# Start the Kafka Consumer in a separate thread
def start_consumer_thread():
    kafka_bootstrap_servers = ['localhost:9092']
    elasticsearch_hosts = ['localhost:9200']
    consumer_thread = Thread(target=consume_and_save_to_elasticsearch, args=(kafka_bootstrap_servers, elasticsearch_hosts))
    consumer_thread.start()


if __name__ == '__main__':
    resource_logger = ResourceLogger(kafka_bootstrap_servers=['localhost:9092'])
    resource_logger.start_scheduler()
    start_consumer_thread()
    app.run(host="0.0.0.0", port=5001)