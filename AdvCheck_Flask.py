from flask import Flask, Response, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import json
MIN_MATCH_COUNT = 10

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['POST'])
@cross_origin()
def AdvCheck():
    # path = './rabbit_choi.png'
    # with open(path, 'rb') as f:
    #     data = f.read()
    
    #*** data가 들어갈 자리에 사용자가 찍은 이미지를 byte로 읽고 JSON에 byteString을 담아서 주면됨!!! ****
    # print(request)
    # req = request.get_json()
    # print(req)
    # data = req['file']
    # # data = request.data

    # print(data)
    # print(type(data))
    data = request.files['file']
    print(type(data), ":", data)
    data_str = data.read()
    #byte 단위 이미지를 cv에 읽히기
    encoded_img = np.fromstring(data_str, dtype = np.uint8)
    print(type(encoded_img))
    img1 = cv.imdecode(encoded_img, 0) # 사용자가 찍은 이미지 
    #cv2.CV_LOAD_IMAGE_UNCHANGED                   
    img2 = cv.imread('test.png',0) # 광고 원본

    # Initiate SIFT detector
    sift = cv.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1,None)
    kp2, des2 = sift.detectAndCompute(img2,None)
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)
    flann = cv.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1,des2,k=2)

    # store all the good matches as per Lowe's ratio test.

    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)
    if len(good)>MIN_MATCH_COUNT: #10개 이상이 일치하면 Okay
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()
        h,w = img1.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        dst = cv.perspectiveTransform(pts,M)
        img2 = cv.polylines(img2,[np.int32(dst)],True,255,3, cv.LINE_AA)
        print("Image match found!")
        draw_params = dict(matchColor = (0,255,0), # draw matches in green color
                        singlePointColor = None,
                        matchesMask = matchesMask, # draw only inliers
                        flags = 2)

        img3 = cv.drawMatches(img1,kp1,img2,kp2,good,None,**draw_params)
        print(type(img3))
        match_result = cv.imencode('.jpg',img3)[1].tobytes()
        print(type(match_result))
        # plt.imshow(img3, 'gray'),plt.show() #보여줄 땐 pyplot으로
        # match_result를 json에 담아서 jsonify 하면 됨
        return jsonify({'match':str(match_result)})
    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        return "Not enough matches are found"
        # matchesMask = None

    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)