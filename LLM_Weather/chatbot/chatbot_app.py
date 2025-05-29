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
    allow_origins=["*"],  # 실제 운영에서는 구체적인 도메인으로 변경
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
    user_id: str = "default_user"  # 기본 사용자 ID
    chat_id: int = None  # 선택적 채팅 세션 ID

class ChatResponse(BaseModel):
    reply: str
    chat_id: int  # 채팅 세션 ID 반환

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """챗봇 메인 페이지"""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'chatbot_ui.html'), 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>chatbot_ui.html 파일을 찾을 수 없습니다.</h1>")

def _convert(value):
    """
    CSV 컬럼이 도(°) 단위면 그대로,
    초/100 단위면 360000으로 나눠 도로 환산한다.
    """
    # 도 단위(0~200)면 그대로 반환
    if value < 200:
        return float(value)
    # 초/100 단위면 도 단위로 변환
    return float(value) / 360000

def find_coords_by_keyword(msg: str):
    """지역 키워드로 좌표 찾기"""
    try:
        for key, alias in REGION_KEYWORDS.items():
            if key in msg:
                # 2단계 또는 3단계에서 검색
                mask = (
                    region_df["2단계"].str.contains(alias, na=False) |
                    region_df["3단계"].str.contains(alias, na=False)
                )
                matching_rows = region_df[mask]
                
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    lat = _convert(row["위도(초/100)"])
                    lon = _convert(row["경도(초/100)"])
                    return {"name": key, "lat": lat, "lon": lon}
        
        return None
    except Exception as e:
        print(f"좌표 검색 오류: {e}")
        return None

def analyze_weather_request(
    message: str,
    client_coords: tuple[float, float] | None = None   # (lat, lon) 튜플, 없으면 None
) -> dict:
    """
    사용자의 메시지를 분석하여
      • location  : '서울'·'춘천'·'노원'·'효자동' or '현재 위치'
      • coords    : (lat, lon) or None
      • weather_type : 'current' | 'forecast' | 'comprehensive'
      • future_hours  : int | None
    를 반환
    """

    # ── 1) 지역 키워드 매칭 ─────────────────────────────
    region_hit = find_coords_by_keyword(message)       # 앞서 정의한 함수
    if region_hit:                                     # 예: {'name':'서울', 'lat':37.57, 'lon':126.98}
        location = region_hit["name"]
        coords   = (region_hit["lat"], region_hit["lon"])
    else:
        # 키워드가 없으면 ⇒ 사용자의 GPS 좌표(없으면 weather_kma에서 fallback)
        location = "현재 위치"
        coords   = client_coords

    # ── 2) 시간(몇 시간 후?) 추출 ─────────────────────
    future_hours = None
    has_future = False
    
    # "N시간 후" 패턴
    time_pattern = r'(\d+)시간?\s*[후뒤]'
    m = re.search(time_pattern, message)
    if m:
        future_hours = int(m.group(1))
        has_future = True
    
    # "내일" 패턴 (약 24시간 후로 계산)
    elif '내일' in message:
        future_hours = 24
        has_future = True
    
    # "모레" 패턴 (약 48시간 후로 계산)  
    elif '모레' in message:
        future_hours = 48
        has_future = True
    
    # "오늘 저녁", "오늘 밤" 등 (6-12시간 후로 추정)
    elif any(word in message for word in ['저녁', '밤', '야간']):
        now_hour = get_korean_time().hour
        if now_hour < 18:  # 오후 6시 전이면
            future_hours = 18 - now_hour  # 저녁까지 남은 시간
        else:
            future_hours = 24 + 18 - now_hour  # 내일 저녁까지
        has_future = True
    
    # "아침" 패턴 (다음날 아침 7시로 가정)
    elif '아침' in message:
        now_hour = get_korean_time().hour
        if now_hour < 7:  # 오전 7시 전이면
            future_hours = 7 - now_hour  # 오늘 아침까지
        else:
            future_hours = 24 + 7 - now_hour  # 내일 아침까지
        has_future = True

    # ── 3) weather_type 결정 ─────────────────────────
    if has_future or any(w in message for w in ['예보', '나중', '앞으로', '미래']):
        weather_type = 'forecast'
    elif any(w in message for w in ['전체', '종합', '자세히', '상세']):
        weather_type = 'comprehensive'
    else:
        weather_type = 'current'

    return {
        "location": location,
        "coords": coords,
        "weather_type": weather_type,
        "future_hours": future_hours,
        "has_future_time": has_future
    }

async def get_cctv_info(message: str) -> str:
    """CCTV 요청 시 CCTV 정보 반환"""
    try:
        # 메시지에서 지역 추출
        cctv_data = await find_nearest_cctv(message)
        
        if cctv_data:
            location_name = cctv_data.get('target_location', '지역')
            distance = cctv_data.get('distance', 0)
            cctv_name = cctv_data.get('cctvname', 'CCTV')
            
            # HTML 생성
            cctv_html = generate_cctv_html(cctv_data)
            
            response = f"📹 {location_name} 근처 CCTV를 찾았어요!\n\n"
            response += f"📍 **{cctv_name}**\n"
            response += f"🗺️ 거리: 약 {distance:.1f}km\n\n"
            response += cctv_html
            
            return response
        else:
            return f"죄송해요. 해당 지역에서 CCTV를 찾을 수 없어요. 😢\n\n다음 지역들을 시도해보세요: 춘천, 효자동, 노원, 서울"
            
    except Exception as e:
        print(f"CCTV 정보 가져오기 오류: {e}")
        return "죄송해요. CCTV 정보를 가져오는 중 오류가 발생했어요. 잠시 후 다시 시도해주세요."

def get_weather_info(weather_request: dict) -> str:
    """날씨 요청 정보에 따라 적절한 날씨 정보 반환"""
    location = weather_request['location']
    weather_type = weather_request['weather_type']
    future_hours = weather_request.get('future_hours', 6)
    
    # 6시간 이후 요청이면 네이버 크롤링 사용 (기상청 초단기예보는 6시간까지만)
    if weather_type == 'forecast' and future_hours and future_hours > 6:
        try:
            weather_info = get_weather_from_naver(location)
            return f"{location}의 {future_hours}시간 후 날씨 정보 (네이버 날씨):\n{weather_info}\n\n⚠️ 6시간 이후 예보는 네이버 날씨를 통해 제공됩니다."
        except Exception as e:
            return f"{location}의 장기 예보 정보를 가져오는데 실패했습니다. 잠시 후 다시 시도해주세요."
    
    # 기상청 API 사용 (API 키가 있는 경우)
    if KMA_SERVICE_KEY:
        try:
            coords = weather_request["coords"]          # (lat, lon) or None
            if weather_type == "current":
                return get_current_weather(KMA_SERVICE_KEY, coords)
            elif weather_type == 'forecast':
                hours = min(future_hours or 6, 6)  # 최대 6시간
                return get_forecast_weather(KMA_SERVICE_KEY, hours)
            elif weather_type == 'comprehensive':
                return get_comprehensive_weather(KMA_SERVICE_KEY)
        except Exception as e:
            print(f"기상청 API 오류: {e}")
            # 기상청 API 실패 시 네이버 크롤링으로 fallback
            pass
    
    # Fallback: 네이버 크롤링 사용
    try:
        weather_info = get_weather_from_naver(location)
        return f"{location}의 날씨 정보:\n{weather_info}\n\n⚠️ 더 정확한 정보를 위해 기상청 API 키를 설정해주세요."
    except Exception as e:
        return f"{location}의 날씨 정보를 가져오는데 실패했습니다. 잠시 후 다시 시도해주세요."

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
            print(f"새 채팅 세션 생성: chat_id={chat_id}, user_id={user_id}")
        
        # 1. 사용자 메시지를 DB에 저장
        user_message_id = ChatMessageRepository.create(
            chat_id=chat_id,
            role="user",
            content=user_message
        )
        print(f"사용자 메시지 저장됨: message_id={user_message_id}")
        
        # Gemini API가 설정되지 않은 경우 기본 응답
        if not GEMINI_API_KEY:
            print("Gemini API 키가 설정되지 않음")
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
                print(f"날씨 요청 분석 결과: {weather_request}")
                
                # 날씨 정보 가져오기
                weather_info = get_weather_info(weather_request)
                
                # 이전 대화 기록 조회 (최근 20개 메시지)
                recent_messages = ChatMessageRepository.get_last_n_messages(chat_id, 20)
                
                # 대화 기록을 문자열로 변환 (현재 메시지 제외)
                conversation_history = ""
                if recent_messages:
                    history_lines = []
                    for msg in recent_messages:
                        role_name = "사용자" if msg['role'] == 'user' else "챗봇"
                        history_lines.append(f"{role_name}: {msg['content']}")
                    conversation_history = "\n".join(history_lines)
                
                # Gemini로 자연스러운 응답 생성
                location_name = weather_request['location'] 
                
                # 대화 기록이 있으면 포함하여 프롬프트 작성
                if conversation_history:
                    prompt = f"""
이전 대화 내용:
{conversation_history}

현재 사용자 질문: "{user_message}"

실제 날씨 정보 (기상청 공식 데이터):
{weather_info}

위 이전 대화 맥락과 현재 날씨 정보를 바탕으로 다음 조건에 맞춰 답변해주세요:
1. 이전 대화의 맥락을 이해하고 연속성 있는 대화로 답변
2. 친근하고 자연스러운 말투로 작성
3. 날씨 정보를 정확하고 이해하기 쉽게 전달
4. 이모지를 적절히 사용해서 친근한 느낌 연출
5. 사용자의 구체적인 질문(시간, 지역 등)에 정확히 대답
6. 답변 길이는 200자 내외로 간결하게

지역 정보: {location_name}
"""
                else:
                    # 첫 대화인 경우 기존 프롬프트 사용
                    prompt = f"""
사용자가 다음과 같이 질문했습니다: "{user_message}"

실제 날씨 정보 (기상청 공식 데이터):
{weather_info}

위 정보를 바탕으로 다음 조건에 맞춰 답변해주세요:
1. 친근하고 자연스러운 말투로 작성
2. 날씨 정보를 정확하고 이해하기 쉽게 전달
3. 이모지를 적절히 사용해서 친근한 느낌 연출
4. 사용자의 구체적인 질문(시간, 지역 등)에 정확히 대답
5. 답변 길이는 200자 내외로 간결하게

지역 정보: {location_name}
"""
                
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text.strip()
                except Exception as e:
                    print(f"Gemini API 오류: {e}")
                    # Gemini API 실패 시 기본 응답
                    bot_response = f"{location_name} 날씨 정보를 전달드릴게요! 🌤️\n\n{weather_info}"
            
            else:
                # 날씨와 무관한 질문에 대한 응답
                available_locations = ", ".join(REGION_KEYWORDS.keys())
                
                # 이전 대화 기록 조회 (최근 20개 메시지)
                recent_messages = ChatMessageRepository.get_last_n_messages(chat_id, 20)
                
                # 대화 기록을 문자열로 변환
                conversation_history = ""
                if recent_messages:
                    history_lines = []
                    for msg in recent_messages:
                        role_name = "사용자" if msg['role'] == 'user' else "챗봇"
                        history_lines.append(f"{role_name}: {msg['content']}")
                    conversation_history = "\n".join(history_lines)
                
                # 대화 기록이 있으면 포함하여 프롬프트 작성
                if conversation_history:
                    prompt = f"""
이전 대화 내용:
{conversation_history}

현재 사용자 질문: "{user_message}"

당신은 날씨 & CCTV 전문 챗봇입니다. 이전 대화의 맥락을 이해하고 연속성 있는 대화로 답변하되, 날씨나 CCTV와 관련되지 않은 질문에는 정중하게 관련 질문을 유도하되, 도움이 될 수 있는 정보는 제공해주세요.

현재 지원하는 지역: {available_locations}

조건:
1. 이전 대화의 맥락을 고려한 연속성 있는 대화
2. 친근하고 도움이 되는 말투 사용
3. 날씨 & CCTV 챗봇의 기능 간단히 소개
4. 이모지 적절히 사용
5. 150자 내외로 간결하게 작성
"""
                else:
                    # 첫 대화인 경우 기존 프롬프트 사용
                    prompt = f"""
사용자가 다음과 같이 질문했습니다: "{user_message}"

당신은 날씨 & CCTV 전문 챗봇입니다. 날씨나 CCTV와 관련되지 않은 질문에는 정중하게 관련 질문을 유도하되, 도움이 될 수 있는 정보는 제공해주세요.

현재 지원하는 지역: {available_locations}

조건:
1. 친근하고 도움이 되는 말투 사용
2. 날씨 & CCTV 챗봇의 기능 간단히 소개
3. 이모지 적절히 사용
4. 150자 내외로 간결하게 작성
"""
                
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text.strip()
                except Exception as e:
                    print(f"Gemini API 오류: {e}")
                    bot_response = f"안녕하세요! 저는 날씨 & CCTV 전문 챗봇이에요. 🌤️📹\n\n현재 {available_locations} 지역의 정확한 날씨 정보와 CCTV를 제공해드릴 수 있어요!\n\n예: '춘천 날씨 알려줘', '춘천 효자동 CCTV 보여줘'"
        
        # 2. 봇 응답을 DB에 저장
        bot_message_id = ChatMessageRepository.create(
            chat_id=chat_id,
            role="assistant",
            content=bot_response
        )
        print(f"봇 응답 저장됨: message_id={bot_message_id}")
        
        return ChatResponse(reply=bot_response, chat_id=chat_id)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"챗봇 오류: {e}")
        raise HTTPException(status_code=500, detail="죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.")

async def get_default_response(message: str) -> str:
    """Gemini API가 없을 때의 기본 응답"""
    weather_keywords = ['날씨', '기온', '온도', '비', '눈', '바람', '예보']
    cctv_keywords = ['cctv', 'CCTV', '씨씨티비', '캠', '카메라', '도로', '교통', '실시간']
    available_locations = ", ".join(REGION_KEYWORDS.keys())

    print("Gemini API가 설정되지 않아 기본 응답 사용")
    
    # CCTV 요청 확인
    if any(keyword in message for keyword in cctv_keywords):
        return await get_cctv_info(message)
    
    # 날씨 요청 확인
    elif any(keyword in message for keyword in weather_keywords):
        # 날씨 요청 분석
        weather_request = analyze_weather_request(message)
        weather_info = get_weather_info(weather_request)
        
        return f"🌤️ 날씨 정보를 전달드릴게요!\n\n{weather_info}"
    else:
        return f"안녕하세요! 저는 날씨 & CCTV 전문 챗봇이에요. 🌤️📹\n\n현재 {available_locations} 지역의 정확한 날씨 정보와 CCTV를 제공해드릴 수 있어요!\n\n예시:\n• '춘천 현재 날씨'\n• '6시간 후 노원 날씨 어때?'\n• '춘천 효자동 CCTV 보여줘'"

@app.get("/api/chat/{chat_id}/messages")
async def get_chat_messages(chat_id: int):
    """특정 채팅의 메시지 기록 조회"""
    try:
        messages = ChatMessageRepository.get_by_chat_id(chat_id)
        return {
            "chat_id": chat_id,
            "messages": messages
        }
    except Exception as e:
        print(f"메시지 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="메시지 조회 중 오류가 발생했습니다.")

@app.get("/api/chats/{user_id}")
async def get_user_chats(user_id: str):
    """사용자의 채팅 목록 조회"""
    try:
        chats = ChatRepository.get_by_user_id(user_id)
        return {
            "user_id": user_id,
            "chats": chats
        }
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
