import sys
import os
from flask import Flask, jsonify
from flask_cors import CORS
from db import db
from routes import routes
from flask import send_from_directory

# 간혹 모듈을 검색할 때 현재 디렉터리의 다른 파일들이 검색 경로에 포함되지 않을 수 있음.
# 문제 없이 같은 폴더 내의 다른 모듈들을 import 하기 위함
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# credential을 포함을 원하는 경우 모든 origin(*)을 사용할 수 없음. 명확한 주소를 입력해야함.

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

app.config.from_object("config")

@app.route('/')
def serve():
    return send_from_directory(os.path.join(app.root_path, 'frontend', 'build'), 'index.html')

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory(os.path.join(app.root_path, 'frontend', 'build'), path)

# 데이터베이스 초기화
db.init_app(app)

# API 라우트 등록
app.register_blueprint(routes)

# 테이블 생성 (app context 안에서)
with app.app_context():
    db.create_all()

# @app.route("/")
# def index():
#     return "Welcome to the AI Interview Helper API!"

@app.route("/api/data")
def api_data():
    return jsonify({"message": "Hello from Flask API!"})

if __name__ == "__main__":
    app.run(debug=True, port=5001)