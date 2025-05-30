import warnings
# urllib3 경고 무시 (macOS LibreSSL 호환성 문제)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.weather import get_weather_from_naver
from repositories.chat_repository import ChatRepository
from repositories.chat_message_repository import ChatMessageRepository

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = FastAPI(
    title="🌤️ 날씨 챗봇 API",
    description="귀여운 날씨 테마의 AI 챗봇",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 구체적인 도메인으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY가 설정되지 않았습니다!")
else:
    genai.configure(api_key=GEMINI_API_KEY, transport="rest")
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

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
            bot_response = get_default_response(user_message)
        else:
            # 날씨 관련 키워드 확인
            weather_keywords = ['날씨', '기온', '온도', '비', '눈', '바람', '습도', '미세먼지', '자외선', '체감온도']
            location_keywords = ['서울', '춘천', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '수원', '고양', '용인', '창원']
            
            is_weather_related = any(keyword in user_message for keyword in weather_keywords)
            
            if is_weather_related:
                # 지역 추출 (기본값: 서울)
                location = '서울'
                for loc in location_keywords:
                    if loc in user_message:
                        location = loc
                        break
                
                # 실제 날씨 정보 가져오기
                weather_info = get_weather_from_naver(location)
                
                # Gemini로 자연스러운 응답 생성
                prompt = f"""
                사용자가 다음과 같이 질문했습니다: "{user_message}"
                
                실제 날씨 정보: {weather_info}
                
                위 정보를 바탕으로 친근하고 자연스러운 말투로 사용자에게 도움이 되는 답변을 해주세요.
                답변은 200자 이내로 간결하게 작성해주세요.
                이모지를 적절히 사용해서 친근한 느낌을 주세요.
                """
                
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text.strip()
                except Exception as e:
                    print(f"Gemini API 오류: {e}")
                    bot_response = f"{location}의 {weather_info} 더 자세한 정보가 필요하시면 말씀해주세요! 🌤️"
            
            else:
                # 날씨와 무관한 질문에 대한 응답
                prompt = f"""
                사용자가 다음과 같이 질문했습니다: "{user_message}"
                
                당신은 날씨 전문 챗봇입니다. 날씨와 관련된 질문이 아닌 경우, 정중하게 날씨 관련 질문을 유도해주세요.
                답변은 100자 이내로 간결하게 작성하고, 친근한 말투를 사용해주세요.
                이모지를 적절히 사용해서 친근한 느낌을 주세요.
                """
                
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text.strip()
                except Exception as e:
                    print(f"Gemini API 오류: {e}")
                    bot_response = "안녕하세요! 저는 날씨 전문 챗봇이에요. 날씨나 기온에 대해 궁금한 것이 있으시면 언제든 물어보세요! 🌤️"
        
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

def get_default_response(message: str) -> str:
    """Gemini API가 없을 때의 기본 응답"""
    weather_keywords = ['날씨', '기온', '온도', '비', '눈', '바람']

    print("Gemini API가 설정되지 않아 기본 응답 사용")
    
    if any(keyword in message for keyword in weather_keywords):
        try:
            weather_info = get_weather_from_naver('서울')
            return f"서울의 {weather_info} 🌤️"
        except Exception as e:
            print(f"날씨 정보 가져오기 실패: {e}")
            return "죄송해요, 현재 날씨 정보를 가져올 수 없어요. 잠시 후 다시 시도해주세요! 😅"
    else:
        return "안녕하세요! 저는 날씨 전문 챗봇이에요. 날씨에 대해 궁금한 것이 있으시면 물어보세요! 🌤️"

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

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "gemini_api": "configured" if GEMINI_API_KEY else "not_configured"
    }

if __name__ == "__main__":
    print(f"🔑 Gemini API 설정: {'✅' if GEMINI_API_KEY else '❌'}")
    print("🌐 http://localhost:8000 에서 확인")
    uvicorn.run("chatbot_app:app", host="0.0.0.0", port=8000, reload=True)
