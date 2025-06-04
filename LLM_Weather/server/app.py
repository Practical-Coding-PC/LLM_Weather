from contextlib import asynccontextmanager
from crawler.naver_news_crawler import export_news_summaries_json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import os
import json
import warnings

from repositories.news_repository import NewsRepository

from chatbot.chatbot_service import ChatbotService
from forecast.forecast_service import ForecastService

# urllib3 경고 무시 (macOS LibreSSL 호환성 문제)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

# Service 인스턴스 생성
chatbot_service = ChatbotService()
forecast_service = ForecastService()

# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    chat_id: int = None

class ChatResponse(BaseModel):
    reply: str
    chat_id: int


#====== FastAPI 요청 파트 ======

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv() # FastAPI를 구동할 때, 환경 변수를 로드한다.
    yield

app = FastAPI(
    title="🌤️📹 날씨 & CCTV 챗봇 API",
    description="기상청 공식 API와 ITS CCTV API 기반 통합 챗봇",
    version="2.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "https://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/weather/news")
async def get_weather_news_summaries(latitude: float, longitude: float):
    """
    주어진 좌표의 지역과 관련된 뉴스를 요약해 반환한다.

    Args:
        latitude (float): 위도.
        longitude (float): 경도.

    Returns:
        dict: 해당 지역과 관련된 뉴스 요약 정보를 기록한 dictionary.
    """
    return json.loads(await export_news_summaries_json(latitude, longitude))

@app.get("/weather/news/test")
async def get_weather_news_summaries_test():
    """
    테스트용으로 특정 지역(춘천)의 뉴스 요약 정보를 반환한다.

    Args:
        없음.

    Returns:
        dict: 춘천 지역과 관련된 뉴스 요약 정보를 기록한 dictionary.
    """
    return NewsRepository.get_by_location("춘천")

@app.get("/weather/ultra_short_term")
async def get_ultra_short_term_weather_forecast(latitude: float, longitude: float):
    """
    주어진 좌표의 초단기 날씨 예보를 반환한다. (기상청 공공 API 활용)

    Args:
        latitude (float): 위도.
        longitude (float): 경도.

    Returns:
        dict: 초단기 날씨 예보 정보를 기록한 dictionary.
    """
    return await forecast_service.get_ultra_short_term_forecast(latitude, longitude)

@app.get("/weather/short_term")
async def get_short_term_weather_forecast(latitude: float, longitude: float):
    """
    주어진 좌표의 단기 날씨 예보를 반환한다. (기상청 공공 API 활용)

    Args:
        latitude (float): 위도.
        longitude (float): 경도.

    Returns:
        dict: 단기 날씨 예보 정보를 기록한 dictionary.
    """
    return await forecast_service.get_short_term_forecast(latitude, longitude)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    챗봇 메인 페이지를 반환한다.
    만약, chatbot_ui.html 파일을 찾지 못하면 "chatbot_ui.html 파일을 찾을 수 없습니다."를 화면에 html로 띄운다.

    Args:
        없음.

    Returns:
        HTMLResponse: 챗봇 UI 페이지의 HTML 콘텐츠.
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), 'chatbot_ui.html'), 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>chatbot_ui.html 파일을 찾을 수 없습니다.</h1>")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    사용자 메시지를 처리하고 챗봇 응답을 반환한다.

    Args:
        request (ChatRequest): 사용자 메시지와 관련된 요청 데이터.

    Returns:
        ChatResponse: 챗봇의 응답 메시지와 채팅 ID를 포함한 데이터.
    """
    try:
        result = await chatbot_service.process_message(
            message=request.message,
            user_id=request.user_id,
            chat_id=request.chat_id
        )
        
        return ChatResponse(reply=result["reply"], chat_id=result["chat_id"])
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"챗봇 오류: {e}")
        raise HTTPException(status_code=500, detail="일시적인 오류가 발생했습니다. 다시 시도해주세요.")

@app.get("/api/chat/{chat_id}/messages")
async def get_chat_messages(chat_id: int):
    """
    특정 채팅의 메시지 기록을 조회한다.

    Args:
        chat_id (int): 채팅 ID.

    Returns:
        dict: 채팅 ID와 메시지를 기록한 dictionary.
    """
    try:
        return chatbot_service.get_chat_messages(chat_id)
    except Exception as e:
        print(f"메시지 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="메시지 조회 중 오류가 발생했습니다.")

@app.get("/api/chats/{user_id}")
async def get_user_chats(user_id: str):
    """
    사용자의 채팅 목록을 조회한다.

    Args:
        user_id (str): 사용자 ID.

    Returns:
        dict: 사용자 ID와 채팅 목록을 기록한 dictionary.
    """
    try:
        return chatbot_service.get_user_chats(user_id)
    except Exception as e:
        print(f"채팅 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="채팅 목록 조회 중 오류가 발생했습니다.")

@app.get("/api/locations")
async def get_supported_locations():
    """
    지원되는 지역 목록을 반환한다.

    Args:
        없음.

    Returns:
        dict: 지원되는 지역 목록과 세부 정보를 기록한 dictionary.
    """
    return chatbot_service.get_supported_locations()

@app.get("/health")
async def health_check():
    """
    서버 상태를 확인한다.
    반환값을 보고 API 키 설정 등이 잘 되었는지를 판단할 수 있다.

    Args:
        없음.

    Returns:
        dict: 서버 상태 및 API 설정 상태를 기록한 dictionary.
    """
    # 환경 변수에서 API 키 상태 확인
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    cctv_api_key = os.getenv('CCTV_API_KEY')
    
    return {
        "status": "healthy",
        "gemini_api": "configured" if gemini_api_key else "not_configured",
        "kma_api": "configured" if forecast_service.is_kma_api_configured() else "not_configured",
        "cctv_api": "configured" if cctv_api_key else "not_configured",
        "supported_locations": forecast_service.get_supported_locations()["locations"]
    }