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
from chatbot.gemini_functions import create_function_calling_model
from chatbot.function_handler import WeatherFunctionHandler
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
        
        # Function Handler 생성
        self.function_handler = WeatherFunctionHandler()
        
        # Gemini 모델 초기화 (Function Calling 지원)
        if self.GEMINI_API_KEY:
            self.model = create_function_calling_model(self.GEMINI_API_KEY)
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
                # 이전 대화 기록 조회
                recent_messages = ChatMessageRepository.get_last_n_messages(chat_id, 20)
                
                # 날씨 요청을 Function Calling으로 처리
                bot_response = await self.handle_weather_with_function_calling(
                    user_message, recent_messages
                )
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
    
    async def handle_weather_with_function_calling(self, user_message: str, recent_messages: list = None) -> str:
        """
        Function Calling을 사용해서 날씨 요청을 처리합니다
        """
        try:
            # 대화 기록 구성
            conversation_history = ""
            if recent_messages:
                history_lines = []
                for msg in recent_messages:
                    role_name = "사용자" if msg['role'] == 'user' else "챗봇"
                    history_lines.append(f"{role_name}: {msg['content']}")
                conversation_history = "\n".join(history_lines)
            
            # Function Calling을 위한 프롬프트
            system_prompt = """당신은 날씨 전문 AI 어시스턴트입니다.
사용자의 날씨 질문을 정확히 분석하고 적절한 날씨 함수를 호출해 주세요.

지원 지역: 춘천, 노원, 서울, 효자동

함수 선택 규칙:
1. "현재 날씨", "지금 날씨", "오늘 날씨", "날씨 어때?" → get_current_weather
2. "N시간 후" (1-6시간) → get_specific_hour_forecast 
3. "N시간 후" (7-120시간) → get_short_term_forecast
4. "종합", "자세히", "전체", "이번 주" → get_comprehensive_weather

중요: 지역명을 정확하게 추출하고, 시간 정보가 있으면 반드시 hours 파라미터를 전달하세요.
함수 호출 후 결과를 친근하고 자연스럽게 요약해주세요."""
            
            if conversation_history:
                full_prompt = f"{system_prompt}\n\n이전 대화:\n{conversation_history}\n\n사용자: {user_message}"
            else:
                full_prompt = f"{system_prompt}\n\n사용자: {user_message}"
            
            print(f"🤖 Function Calling 시작: {user_message}")
            
            # Gemini에게 메시지 전송
            response = self.model.generate_content(full_prompt)
            
            # Function Call이 있는지 확인
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        # Function Call 실행
                        function_name = part.function_call.name
                        function_args = {}
                        
                        # 인자 추출
                        for key, value in part.function_call.args.items():
                            function_args[key] = value
                        
                        print(f"🔥 Function Call 세부사항:")
                        print(f"  - 함수명: {function_name}")
                        print(f"  - 인자: {function_args}")
                        
                        # 함수 실행
                        function_result = self.function_handler.execute_function(
                            function_name, function_args
                        )
                        
                        print(f"🌟 Function 결과 내용:")
                        print(f"  - 결과 길이: {len(function_result)} 문자")
                        print(f"  - 결과 미리보기: {function_result[:100]}...")
                        
                        # 결과를 Gemini에게 다시 전송해서 자연스러운 응답 생성
                        final_prompt = f"""사용자 질문: "{user_message}"

날씨 데이터:
{function_result}

위 날씨 데이터를 바탕으로 사용자의 질문에 정확하고 친근하게 답변해주세요.

답변 가이드라인:
- 사용자가 묻는 시간대의 날씨에 집중해서 답변
- 기온, 하늘상태, 강수확률 등 핵심 정보 포함
- 친근하고 자연스러운 말투
- 100-150자 내외로 간결하게 작성
- 이모지나 기호 사용하여 더 친근하게"""
                        
                        # 새로운 모델 인스턴스로 최종 응답 생성 (Function Calling 없이)
                        import google.generativeai as genai
                        simple_model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
                        final_response = simple_model.generate_content(final_prompt)
                        
                        return final_response.text.strip()
                
                # Function Call이 없으면 일반 텍스트 응답
                if response.text:
                    return response.text.strip()
            
            return "죄송합니다. 날씨 정보를 가져오는데 문제가 발생했습니다."
            
        except Exception as e:
            print(f"Function Calling 오류: {e}")
            # Fallback: 기존 방식으로 처리
            weather_request = self.forecast_service.analyze_weather_request(user_message)
            weather_info = self.forecast_service.get_weather_info(weather_request)
            return f"날씨 정보:\n\n{weather_info}"
    
    def get_supported_locations(self) -> Dict[str, Any]:
        """
        지원되는 지역 목록을 반환한다.
        """
        return self.forecast_service.get_supported_locations()
 