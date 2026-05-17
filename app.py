from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
import cv2

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/stitch', methods=['POST', 'OPTIONS'])
def stitch():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json()
    frames_b64 = data.get('frames', [])
    if len(frames_b64) == 0:
        return jsonify({'status': 'error', 'message': 'No frames'}), 400
    images = []
    for b64 in frames_b64:
        if ',' in b64:
            b64 = b64.split(',')[1]
        img_bytes = base64.b64decode(b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is not None:
            images.append(img)
    if len(images) == 0:
        return jsonify({'status': 'error', 'message': 'No valid images'}), 400
    if len(images) == 1:
        _, buffer = cv2.imencode('.jpg', images[0])
        result_b64 = base64.b64encode(buffer).decode('utf-8')
    else:
        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        status, panorama = stitcher.stitch(images)
        if status == cv2.Stitcher_OK:
            _, buffer = cv2.imencode('.jpg', panorama)
            result_b64 = base64.b64encode(buffer).decode('utf-8')
        else:
            _, buffer = cv2.imencode('.jpg', images[0])
            result_b64 = base64.b64encode(buffer).decode('utf-8')
    return jsonify({
        'status': 'ok',
        'image': 'data:image/jpeg;base64,' + result_b64,
        'count': len(images)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)