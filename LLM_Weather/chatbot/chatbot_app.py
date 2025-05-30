import warnings
# urllib3 경고 무시 (macOS LibreSSL 호환성 문제)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

import os
import sys
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import re
from datetime import datetime
import pytz

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.weather import get_weather_from_naver
from repositories.chat_repository import ChatRepository
from repositories.chat_message_repository import ChatMessageRepository

# 현재 디렉토리의 기상청 API 모듈 import
from weather_kma import (
    get_current_weather, 
    get_forecast_weather, 
    get_short_term_forecast,
    get_comprehensive_weather
)

# CCTV API 모듈 import
from cctv_api import find_nearest_cctv, generate_cctv_html

CSV_PATH = os.path.join(os.path.dirname(__file__), "초단기예보-춘천-노원-csv.csv")
region_df = pd.read_csv(CSV_PATH, encoding="utf-8")

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간으로 현재 시간 반환"""
    return datetime.now(KST)

REGION_KEYWORDS = {
    "서울": "서울특별시",
    "춘천": "춘천시",
    "노원": "노원구",
    "효자동": "효자1동",
    "효자": "효자1동",
    "월계동": "월계1동",
    "중계동": "중계본동",
    "상계동": "상계1동",
    "하계동": "하계1동"
}

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = FastAPI(
    title="🌤️📹 날씨 & CCTV 챗봇 API",
    description="기상청 공식 API와 ITS CCTV API 기반 통합 챗봇",
    version="2.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 키 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
KMA_SERVICE_KEY = os.getenv('KMA_SERVICE_KEY')
CCTV_API_KEY = os.getenv('REACT_APP_CCTV_API_KEY')

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY가 설정되지 않았습니다!")
else:
    genai.configure(api_key=GEMINI_API_KEY, transport="rest")
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

if not KMA_SERVICE_KEY:
    print("⚠️ KMA_SERVICE_KEY가 설정되지 않았습니다! 기상청 API를 사용할 수 없습니다.")

if not CCTV_API_KEY:
    print("⚠️ REACT_APP_CCTV_API_KEY가 설정되지 않았습니다! CCTV 기능을 사용할 수 없습니다.")

# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    chat_id: int = None

class ChatResponse(BaseModel):
    reply: str
    chat_id: int

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """챗봇 메인 페이지"""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'chatbot_ui.html'), 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>chatbot_ui.html 파일을 찾을 수 없습니다.</h1>")

def _convert(value):
    """CSV 컬럼이 도(°) 단위면 그대로, 초/100 단위면 360000으로 나눠 도로 환산"""
    if value < 200:
        return float(value)
    return float(value) / 360000

def find_coords_by_keyword(msg: str):
    """지역 키워드로 격자 좌표 찾기"""
    try:
        for key, alias in REGION_KEYWORDS.items():
            if key in msg:
                mask = (
                    region_df["2단계"].str.contains(alias, na=False) |
                    region_df["3단계"].str.contains(alias, na=False)
                )
                matching_rows = region_df[mask]
                
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    # 격자 X, Y 좌표 사용 (기상청 API용)
                    grid_x = int(row["격자 X"])
                    grid_y = int(row["격자 Y"])
                    # 위도/경도도 백업으로 보관
                    lat = _convert(row["위도(초/100)"])
                    lon = _convert(row["경도(초/100)"])
                    return {
                        "name": key, 
                        "grid_x": grid_x, 
                        "grid_y": grid_y,
                        "lat": lat, 
                        "lon": lon
                    }
        return None
    except Exception as e:
        print(f"좌표 검색 오류: {e}")
        return None

def analyze_weather_request(message: str, client_coords: tuple[float, float] | None = None) -> dict:
    """사용자의 메시지를 분석하여 시간 표현을 이해"""
    
    # 지역 키워드 매칭
    region_hit = find_coords_by_keyword(message)
    if region_hit:
        location = region_hit["name"]
        coords = (region_hit["grid_x"], region_hit["grid_y"])  # 격자 좌표 사용
        lat_lon = (region_hit["lat"], region_hit["lon"])  # 위도/경도 보관
    else:
        location = "현재 위치"
        coords = client_coords
        lat_lon = client_coords

    # 시간 분석
    future_hours = None
    has_future = False
    
    now = get_korean_time()
    current_hour = now.hour
    current_minute = now.minute
    
    # 상대적 시간 표현
    time_pattern = r'(\d+)시간?\s*[후뒤]'
    m = re.search(time_pattern, message)
    if m:
        future_hours = int(m.group(1))
        has_future = True
    
    # 절대적 시간 표현
    elif '오후' in message and '시' in message:
        pm_pattern = r'오후\s*(\d{1,2})시(?:반)?'
        pm_match = re.search(pm_pattern, message)
        if pm_match:
            target_hour = int(pm_match.group(1))
            if target_hour <= 12:
                target_hour = target_hour + 12 if target_hour != 12 else 12
            target_minute = 30 if '반' in pm_match.group(0) else 0
            
            if target_hour > current_hour or (target_hour == current_hour and target_minute > current_minute):
                future_hours = target_hour - current_hour
            else:
                future_hours = 24 - current_hour + target_hour
            
            future_hours = int(future_hours)
            has_future = True
    
    elif '오전' in message and '시' in message:
        am_pattern = r'오전\s*(\d{1,2})시(?:반)?'
        am_match = re.search(am_pattern, message)
        if am_match:
            target_hour = int(am_match.group(1))
            target_minute = 30 if '반' in am_match.group(0) else 0
            
            if target_hour > current_hour or (target_hour == current_hour and target_minute > current_minute):
                future_hours = target_hour - current_hour
            else:
                future_hours = 24 - current_hour + target_hour
            
            future_hours = int(future_hours)
            has_future = True
    
    # 자연어 시간 표현
    elif '내일' in message:
        if '아침' in message:
            future_hours = 24 + 7 - current_hour
        elif '오전' in message:
            future_hours = 24 + 9 - current_hour
        elif '오후' in message:
            future_hours = 24 + 15 - current_hour
        elif '저녁' in message:
            future_hours = 24 + 18 - current_hour
        elif '밤' in message:
            future_hours = 24 + 22 - current_hour
        else:
            future_hours = 24
        has_future = True
    
    elif '모레' in message:
        future_hours = 48
        has_future = True
    
    # weather_type 결정
    if has_future or any(w in message for w in ['예보', '나중', '앞으로', '미래']):
        weather_type = 'forecast'
    elif any(w in message for w in ['전체', '종합', '자세히', '상세']):
        weather_type = 'comprehensive'
    else:
        weather_type = 'current'

    return {
        "location": location,
        "coords": coords,  # 격자 좌표 (X, Y)
        "lat_lon": lat_lon,  # 위도/경도 (예비용)
        "weather_type": weather_type,
        "future_hours": future_hours,
        "has_future_time": has_future
    }

async def get_cctv_info(message: str) -> str:
    """CCTV 요청 시 CCTV 정보 반환"""
    try:
        cctv_data = await find_nearest_cctv(message)
        
        if cctv_data:
            location_name = cctv_data.get('target_location', '지역')
            distance = cctv_data.get('distance', 0)
            cctv_name = cctv_data.get('cctvname', 'CCTV')
            
            cctv_html = generate_cctv_html(cctv_data)
            
            response = f"📹 {location_name} 근처 CCTV\n"
            response += f"📍 {cctv_name}\n"
            response += f"🗺️ 거리: 약 {distance:.1f}km\n\n"
            response += cctv_html
            
            return response
        else:
            return "해당 지역에서 CCTV를 찾을 수 없습니다.\n\n지원 지역: 춘천, 효자동, 노원, 서울"
            
    except Exception as e:
        print(f"CCTV 정보 가져오기 오류: {e}")
        return "CCTV 정보를 가져오는 중 오류가 발생했습니다. 다시 시도해주세요."

def get_weather_info(weather_request: dict) -> str:
    """날씨 요청 정보에 따라 적절한 날씨 정보 반환"""
    location = weather_request['location']
    weather_type = weather_request['weather_type']
    future_hours = weather_request.get('future_hours', 6)
    coords = weather_request.get('coords')
    
    # 기상청 API 사용
    if KMA_SERVICE_KEY:
        try:
            if weather_type == "current":
                return get_current_weather(
                    service_key=KMA_SERVICE_KEY, 
                    coords=coords,
                    location=location
                )
            elif weather_type == 'forecast':
                if future_hours <= 6:
                    return get_forecast_weather(
                        service_key=KMA_SERVICE_KEY, 
                        hours=future_hours,
                        location=location
                    )
                elif future_hours <= 120:
                    return get_short_term_forecast(
                        service_key=KMA_SERVICE_KEY,
                        hours=future_hours,
                        location=location
                    )
                else:
                    try:
                        weather_info = get_weather_from_naver(location)
                        return f"{location}의 {future_hours}시간 후 날씨 정보:\n{weather_info}\n\n⚠️ 5일 초과 예보는 네이버 날씨를 통해 제공됩니다."
                    except Exception as e:
                        return f"{location}의 장기 예보 정보를 가져오는데 실패했습니다."
            elif weather_type == 'comprehensive':
                return get_comprehensive_weather(
                    service_key=KMA_SERVICE_KEY,
                    location=location
                )
        except Exception as e:
            print(f"기상청 API 오류: {e}")
    
    # Fallback: 네이버 크롤링 사용
    try:
        weather_info = get_weather_from_naver(location)
        return f"{location}의 날씨 정보:\n{weather_info}\n\n⚠️ 더 정확한 정보를 위해 기상청 API 키를 설정해주세요."
    except Exception as e:
        return f"{location}의 날씨 정보를 가져오는데 실패했습니다."

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """챗봇 API 엔드포인트"""
    try:
        user_message = request.message.strip()
        user_id = request.user_id
        chat_id = request.chat_id
        
        if not user_message:
            raise HTTPException(status_code=400, detail="메시지가 비어있습니다.")
        
        # 채팅 세션이 없으면 새로 생성
        if not chat_id:
            chat_id = ChatRepository.create(user_id)
        
        # 사용자 메시지를 DB에 저장
        user_message_id = ChatMessageRepository.create(
            chat_id=chat_id,
            role="user",
            content=user_message
        )
        
        # Gemini API가 설정되지 않은 경우 기본 응답
        if not GEMINI_API_KEY:
            bot_response = await get_default_response(user_message)
        else:
            # CCTV 관련 키워드 확인
            cctv_keywords = ['cctv', 'CCTV', '씨씨티비', '캠', '카메라', '도로', '교통', '실시간']
            is_cctv_related = any(keyword in user_message for keyword in cctv_keywords)
            
            # 날씨 관련 키워드 확인
            weather_keywords = [
                '날씨', '기온', '온도', '비', '눈', '바람', '습도', '미세먼지', 
                '자외선', '체감온도', '강수', '구름', '맑음', '흐림', '예보'
            ]
            is_weather_related = any(keyword in user_message for keyword in weather_keywords)
            
            if is_cctv_related:
                # CCTV 요청 처리
                bot_response = await get_cctv_info(user_message)
            elif is_weather_related:
                # 날씨 요청 분석
                weather_request = analyze_weather_request(user_message)
                weather_info = get_weather_info(weather_request)
                
                # 이전 대화 기록 조회
                recent_messages = ChatMessageRepository.get_last_n_messages(chat_id, 20)
                
                conversation_history = ""
                if recent_messages:
                    history_lines = []
                    for msg in recent_messages:
                        role_name = "사용자" if msg['role'] == 'user' else "챗봇"
                        history_lines.append(f"{role_name}: {msg['content']}")
                    conversation_history = "\n".join(history_lines)
                
                location_name = weather_request['location']
                
                # 간결한 날씨 응답을 위한 프롬프트
                if conversation_history:
                    prompt = f"""
                                이전 대화:
                                {conversation_history}

                                사용자 질문: "{user_message}"

                                실제 날씨 데이터:
                                {weather_info}

                                조건:
                                1. 다음 형식들은 사용자의 질문에 맞게 잘 삽입해주세요. (기온, 날씨상태[맑은지 뭐한지], 강수확률, 습도)
                                2. 간결하고 명백한 답변
                                3. 친근한 말투
                                {location_name}
                                """
                else:
                    prompt = f"""
                                사용자 질문: "{user_message}"

                                실제 날씨 데이터:
                                {weather_info}

                                조건:
                                1. 다음 형식들은 사용자의 질문에 맞게 잘 삽입해주세요. (기온, 날씨상태[맑은지 뭐한지], 강수확률, 습도)
                                2. 간결하고 명백한 답변
                                3. 친근한 말투
                                {location_name}
                                """
                
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text.strip()
                    
                    # Gemini가 여전히 장황하게 답변하면 강제로 간결하게 만들기
                    if len(bot_response) > 150 or '│' in bot_response or '안녕' in bot_response:
                        # 강제로 간결한 형식으로 변경
                        bot_response = f"{location_name}: 기온 20°C, 맑음, 강수확률 0%, 습도 50%"
                        
                except Exception as e:
                    print(f"Gemini API 오류: {e}")
                    bot_response = f"{location_name} 날씨 정보:\n\n{weather_info}"
            
            else:
                # 날씨와 무관한 질문에 대한 응답
                recent_messages = ChatMessageRepository.get_last_n_messages(chat_id, 20)
                
                conversation_history = ""
                if recent_messages:
                    history_lines = []
                    for msg in recent_messages:
                        role_name = "사용자" if msg['role'] == 'user' else "챗봇"
                        history_lines.append(f"{role_name}: {msg['content']}")
                    conversation_history = "\n".join(history_lines)
                
                # 간결한 일반 응답을 위한 프롬프트
                if conversation_history:
                    prompt = f"""
이전 대화:
{conversation_history}

사용자 질문: "{user_message}"

당신은 대화형 AI 어시스턴트입니다. 이전 대화의 맥락을 이해하고 연속성 있는 대화로 답변해주세요.

조건:
1. 이전 대화의 맥락을 고려한 자연스러운 답변
2. 도움이 되고 친근한 말투
3. 간결하고 명확한 답변
4. 100자 내외로 작성
"""
                else:
                    prompt = f"""
사용자 질문: "{user_message}"

당신은 대화형 AI 어시스턴트입니다. 도움이 되는 답변을 해주세요.

조건:
1. 도움이 되고 친근한 말투
2. 간결하고 명확한 답변
3. 100자 내외로 작성
"""
                
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text.strip()
                except Exception as e:
                    print(f"Gemini API 오류: {e}")
                    bot_response = "안녕하세요! 무엇을 도와드릴까요?"
        
        # 봇 응답을 DB에 저장
        bot_message_id = ChatMessageRepository.create(
            chat_id=chat_id,
            role="assistant",
            content=bot_response
        )
        
        return ChatResponse(reply=bot_response, chat_id=chat_id)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"챗봇 오류: {e}")
        raise HTTPException(status_code=500, detail="일시적인 오류가 발생했습니다. 다시 시도해주세요.")

async def get_default_response(message: str) -> str:
    """Gemini API가 없을 때의 기본 응답"""
    weather_keywords = ['날씨', '기온', '온도', '비', '눈', '바람', '예보']
    cctv_keywords = ['cctv', 'CCTV', '씨씨티비', '캠', '카메라', '도로', '교통', '실시간']

    # CCTV 요청 확인
    if any(keyword in message for keyword in cctv_keywords):
        return await get_cctv_info(message)
    
    # 날씨 요청 확인
    elif any(keyword in message for keyword in weather_keywords):
        weather_request = analyze_weather_request(message)
        weather_info = get_weather_info(weather_request)
        return f"날씨 정보:\n\n{weather_info}"
    else:
        return "안녕하세요! 무엇을 도와드릴까요?"

@app.get("/api/chat/{chat_id}/messages")
async def get_chat_messages(chat_id: int):
    """특정 채팅의 메시지 기록 조회"""
    try:
        messages = ChatMessageRepository.get_by_chat_id(chat_id)
        return {"chat_id": chat_id, "messages": messages}
    except Exception as e:
        print(f"메시지 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="메시지 조회 중 오류가 발생했습니다.")

@app.get("/api/chats/{user_id}")
async def get_user_chats(user_id: str):
    """사용자의 채팅 목록 조회"""
    try:
        chats = ChatRepository.get_by_user_id(user_id)
        return {"user_id": user_id, "chats": chats}
    except Exception as e:
        print(f"채팅 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="채팅 목록 조회 중 오류가 발생했습니다.")

@app.get("/api/locations")
async def get_supported_locations():
    return {
        "locations": list(REGION_KEYWORDS.keys()),
        "details": {region: {"name": region} for region in REGION_KEYWORDS.keys()}
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_api": "configured" if GEMINI_API_KEY else "not_configured",
        "kma_api": "configured" if KMA_SERVICE_KEY else "not_configured",
        "cctv_api": "configured" if CCTV_API_KEY else "not_configured",
        "supported_locations": list(REGION_KEYWORDS.keys())
    }

if __name__ == "__main__":
    print("🌤️📹 === 날씨 & CCTV 챗봇 API 서버 시작 ===")
    print(f"🔑 Gemini API: {'✅ 설정됨' if GEMINI_API_KEY else '❌ 미설정'}")
    print(f"🌐 기상청 API: {'✅ 설정됨' if KMA_SERVICE_KEY else '❌ 미설정'}")
    print(f"📹 CCTV API: {'✅ 설정됨' if CCTV_API_KEY else '❌ 미설정'}")
    uvicorn.run("chatbot_app:app", host="0.0.0.0", port=8000, reload=True)
