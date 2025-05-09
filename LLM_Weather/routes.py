from flask import Blueprint, request, jsonify
import google.generativeai as genai
import sys
import os
from db import db
from models import InterviewRecord
from config import GEMINI_API_KEY
# from utils.embedding import get_embedding
from utils.weather import get_weather_from_naver
from flask_cors import CORS

sys.path.append(os.path.join(os.path.dirname(__file__), "index"))
from index.faiss_index import search

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("models/gemini-1.5-pro")

routes = Blueprint("api_routes", __name__)
CORS(routes, supports_credentials=True)

#  🔸간단한 캐시 (선택적)
question_cache = {}

@routes.route("/get_weather", methods=["POST", "OPTIONS"])
def get_weather():
    if request.method == "OPTIONS":
        # 생략된 preflight 처리...
        return jsonify(...)

    try:
        data = request.json
        user_message = data.get("user_message", "오늘 서울 날씨 어때?").strip()

        # 🌤️ 실제 날씨 크롤링
        weather_info = get_weather_from_naver(user_message)

        # Gemini 프롬프트 구성
        prompt = f"""
            다음은 사용자가 요청한 날씨 정보입니다: "{user_message}"

            실제 날씨 데이터를 기반으로 다음 정보를 사용자에게 친절하게 전달해 주세요.

            🔸 실제 날씨 정보:
            {weather_info}

            친절하고 자연스러운 말투로 요약해서 알려주세요.
                    """

        response = model.generate_content(prompt)
        reply = response.text.strip()

        return jsonify({"reply": reply})

    except Exception as e:
        print("Error 발생:", str(e))
        return jsonify({"error": "날씨 응답 생성 중 문제가 발생했습니다."}), 500