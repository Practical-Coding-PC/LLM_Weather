from contextlib import asynccontextmanager
from crawler.naver_news_crawler import export_news_summaries_json
from forecast.ultra_short_term_forecast import fetch_ultra_short_term_forecast
from forecast.short_term_forecast import fetch_short_term_forecast
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

import os
import json
import warnings

from repositories.user_repository import UserRepository
from repositories.notification_repository import NotificationRepository
from repositories.user_repository import UserRepository

from chatbot.chatbot_service import ChatbotService
from forecast.forecast_service import ForecastService
from forecast.push_weather_notification import push_weather_notification

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
    latitude: float = None
    longitude: float = None

class ChatResponse(BaseModel):
    reply: str
    chat_id: int

class CreateUserRequest(BaseModel):
    location: str

class CreateNotificationRequest(BaseModel):
    user_id: int
    endpoint: str
    expirationTime: int = None
    p256dh: str
    auth: str

class NotificationTestRequest(BaseModel):
    userId: str

#====== FastAPI 요청 파트 ======

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI를 구동할 때, 환경 변수를 로드한다.
    load_dotenv()

    # 날씨 알림 스케줄러 설정 (30분마다)
    scheduler.add_job(
        push_weather_notification,
        'interval',
        minutes=30,
        id='weather_notification_job'
    )
    
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
            chat_id=request.chat_id,
            latitude=request.latitude,
            longitude=request.longitude
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

@app.post("/users")
async def create_user(request: CreateUserRequest):
    """
    사용자를 생성한다.
    """
    try:
        # 사용자 생성
        user_id = UserRepository.create(request.location)
        
        result = {
            "user_id": user_id,
            "location": request.location
        }
        
        return result
        
    except Exception as e:
        print(f"사용자 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="사용자 생성 중 오류가 발생했습니다.")

@app.post("/notifications")
async def create_notification(request: CreateNotificationRequest):
    """
    사용자의 알림 구독을 설정한다.
    """
    try:
        notification_id = NotificationRepository.create(
            user_id=request.user_id,
            endpoint=request.endpoint,
            expiration_time=request.expirationTime,
            p256dh_key=request.p256dh,
            auth_key=request.auth
        )
        
        result = {
            "notification_id": notification_id,
        }
        
        return result
        
    except Exception as e:
        print(f"알림 구독 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="알림 구독 생성 중 오류가 발생했습니다.")

@app.post("/notification-test")
async def send_notification_test(request: NotificationTestRequest):
    """
    사용자에게 테스트 알림을 전송한다.
    notifications 테이블에서 구독 정보를 가져와 Next.js의 /notify 엔드포인트로 요청을 보낸다.
    """
    try:
        import httpx
        
        # 사용자 ID로 알림 구독 정보 조회
        subscriptions = NotificationRepository.get_by_user_id(int(request.userId))
        
        if not subscriptions:
            raise HTTPException(status_code=404, detail="해당 사용자의 알림 구독 정보를 찾을 수 없습니다.")
        
        # 첫 번째 (유일한) 구독 정보 가져오기
        subscription = subscriptions[0]
        
        # webpush 구독 객체 구성
        subscription_obj = {
            "endpoint": subscription['endpoint'],
            "p256dh": subscription['p256dh_key'],
            "auth": subscription['auth_key']
        }
        
        # Next.js /notify 엔드포인트로 POST 요청
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:3001/notify",
                json={
                    "subscription": subscription_obj,
                    "message": "곧 비나 눈이 올 수 있어요 ☔ 외출에 주의하세요!"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"알림 전송 실패: HTTP {response.status_code}")
        
        return {
            "success": True,
            "message": "테스트 알림을 성공적으로 전송했습니다."
        }
        
    except HTTPException as e:
        print(f"HTTPException 발생: {e}")
        raise
    except Exception as e:
        print(f"알림 테스트 오류: {e}")
        raise HTTPException(status_code=500, detail="알림 테스트 중 오류가 발생했습니다.")

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
