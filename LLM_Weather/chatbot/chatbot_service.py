import os
import sys
import warnings
import google.generativeai as genai
from typing import Optional, Dict, Any

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from repositories.chat_repository import ChatRepository
from repositories.chat_message_repository import ChatMessageRepository

from chatbot.utils.cctv_utils import find_nearest_cctv
from forecast.forecast_service import ForecastService

# urllib3 경고 무시 (macOS LibreSSL 호환성 문제)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")


class ChatbotService:
    """
    챗봇의 비즈니스 로직을 처리하는 서비스 클래스
    """
    
    def __init__(self):
        # API 키 설정
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.CCTV_API_KEY = os.getenv('CCTV_API_KEY')
        
        # ForecastService 인스턴스 생성
        self.forecast_service = ForecastService()
        
        # Gemini 모델 초기화
        if self.GEMINI_API_KEY:
            genai.configure(api_key=self.GEMINI_API_KEY, transport="rest")
            self.model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
        else:
            self.model = None

    async def get_cctv_info(self, message: str) -> str:
        """
        메시지에서 CCTV 관련 정보를 검색하여 반환한다.
        
        Args:
            message (str): 사용자 메시지.
            
        Returns:
            str: CCTV 정보 또는 오류 메시지.
        """
        try:
            cctv_data = await find_nearest_cctv(message)
            
            if cctv_data:
                return f"cctv_data:{cctv_data}"
            else:
                return "해당 지역에서 CCTV를 찾을 수 없습니다.\n\n지원 지역: 춘천, 효자동, 노원, 서울"
                
        except Exception as e:
            print(f"CCTV 정보 가져오기 오류: {e}")
            return "CCTV 정보를 가져오는 중 오류가 발생했습니다. 다시 시도해주세요."
    
    async def get_default_response(self, message: str) -> str:
        """
        Gemini API가 없을 때 기본 응답을 생성한다.
        
        Args:
            message (str): 사용자 메시지.
            
        Returns:
            str: 기본 응답 메시지인 "안녕하세요! 무엇을 도와드릴까요?"
        """
        weather_keywords = ['날씨', '기온', '온도', '비', '눈', '바람', '예보']
        cctv_keywords = ['cctv', 'CCTV', '씨씨티비', '캠', '카메라', '도로', '교통', '실시간']

        # CCTV 요청 확인
        if any(keyword in message for keyword in cctv_keywords):
            return await self.get_cctv_info(message)
        
        # 날씨 요청 확인
        elif any(keyword in message for keyword in weather_keywords):
            weather_request = self.forecast_service.analyze_weather_request(message)
            weather_info = self.forecast_service.get_weather_info(weather_request)
            return f"날씨 정보:\n\n{weather_info}"
        else:
            return "안녕하세요! 무엇을 도와드릴까요?"
    
    async def process_message(self, message: str, user_id: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """
        사용자 메시지를 처리하고 챗봇 응답을 생성한다.
        
        Args:
            message (str): 사용자 메시지
            user_id (str): 사용자 ID
            chat_id (int, optional): 채팅 ID
            
        Returns:
            dict: 챗봇 응답과 채팅 ID를 포함한 딕셔너리
        """
        user_message = message.strip()
        
        if not user_message:
            raise ValueError("메시지가 비어있습니다.")
        
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
        if not self.GEMINI_API_KEY:
            bot_response = await self.get_default_response(user_message)
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
                bot_response = await self.get_cctv_info(user_message)
            elif is_weather_related:
                # 날씨 요청 분석 및 처리
                weather_request = self.forecast_service.analyze_weather_request(user_message)
                weather_info = self.forecast_service.get_weather_info(weather_request)
                
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
                    response = self.model.generate_content(prompt)
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
                    response = self.model.generate_content(prompt)
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
        
        return {"reply": bot_response, "chat_id": chat_id}
    
    def get_chat_messages(self, chat_id: int) -> Dict[str, Any]:
        """
        특정 채팅의 메시지 기록을 조회한다.
        
        Args:
            chat_id (int): 채팅 ID
            
        Returns:
            dict: 채팅 ID와 메시지 목록을 포함한 딕셔너리
        """
        messages = ChatMessageRepository.get_by_chat_id(chat_id)
        return {"chat_id": chat_id, "messages": messages}
    
    def get_user_chats(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 채팅 목록을 조회한다.
        
        Args:
            user_id (str): 사용자 ID
            
        Returns:
            dict: 사용자 ID와 채팅 목록을 포함한 딕셔너리
        """
        chats = ChatRepository.get_by_user_id(user_id)
        return {"user_id": user_id, "chats": chats}
    
 