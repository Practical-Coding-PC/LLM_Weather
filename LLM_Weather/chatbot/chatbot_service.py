import os
import sys
import warnings
import google.generativeai as genai
from typing import Optional, Dict, Any

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from repositories.chat_repository import ChatRepository
from repositories.chat_message_repository import ChatMessageRepository
from forecast.forecast_service import ForecastService

# 리팩토링된 모듈들 import
from chatbot.utils.function_tools import WeatherFunctionTools
from chatbot.utils.prompt_builder import PromptBuilder
from chatbot.utils.function_executor import FunctionExecutor

# urllib3 경고 무시 (macOS LibreSSL 호환성 문제)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")


class ChatbotService:
    """
    챗봇의 비즈니스 로직을 처리하는 서비스 클래스
    """
    
    def __init__(self):
        # API 키 설정
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        
        # 서비스 인스턴스 생성
        self.forecast_service = ForecastService()
        self.function_executor = FunctionExecutor(self.forecast_service)
        
        # Function calling tools 가져오기
        self.weather_tools = WeatherFunctionTools.get_weather_tools()
        
        # Gemini 모델 초기화
        if self.GEMINI_API_KEY:
            genai.configure(api_key=self.GEMINI_API_KEY, transport="rest")
            self.model = genai.GenerativeModel(
                "models/gemini-1.5-flash-latest",
                tools=self.weather_tools
            )
        else:
            self.model = None


    
    async def process_message(self, message: str, user_id: str, chat_id: Optional[int] = None, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
        """
        사용자 메시지를 처리하고 챗봇 응답을 생성한다.
        
        Args:
            message (str): 사용자 메시지
            user_id (str): 사용자 ID
            chat_id (int, optional): 채팅 ID
            latitude (float, optional): 사용자의 현재 위치 좌표 위도
            longitude (float, optional): 사용자의 현재 위치 좌표 경도
            
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
            bot_response = "안녕하세요! 무엇을 도와드릴까요?"
        else:
            # 이전 대화 기록 조회
            recent_messages = ChatMessageRepository.get_last_n_messages(chat_id, 10)

            conversation_history = ""
            if recent_messages:
                history_lines = []
                for msg in recent_messages:
                    role_name = "사용자" if msg['role'] == 'user' else "챗봇"
                    history_lines.append(f"{role_name}: {msg['content']}")
                conversation_history = "\n".join(history_lines)
            
            # Function calling을 위한 프롬프트 생성
            prompt = PromptBuilder.build_function_call_prompt(user_message, conversation_history)
            
            try:
                response = self.model.generate_content(prompt)
                
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            print(f"Function call detected: {part.function_call.name}")
                            # Function call 실행
                            function_name = part.function_call.name
                            function_args = {}
                            for key, value in part.function_call.args.items():
                                function_args[key] = value
                            
                            print(f"Executing function: {function_name} with args: {function_args}")
                            
                            # 함수 실행 (위치 정보 포함)
                            function_result = await self.function_executor.execute_function(
                                function_name, 
                                function_args, 
                                latitude,
                                longitude
                            )
                            
                            # 결과를 바탕으로 최종 응답 생성
                            if function_name in ["get_location_coordinates", "get_cctv_info"]:
                                # 위치 조회 및 CCTV 함수의 경우 직접 결과를 반환
                                bot_response = function_result
                            else:
                                # 날씨 함수의 경우 LLM에게 데이터를 해석하도록 요청
                                final_prompt = PromptBuilder.build_final_response_prompt(user_message, function_result)
                                final_response = self.model.generate_content(final_prompt)
                                bot_response = final_response.text.strip()
                            break
                    else:
                        # Function call이 없으면 일반 대화
                        print("No function call detected, using direct response")
                        bot_response = response.text.strip()
                else:
                    bot_response = "죄송합니다. 응답을 생성할 수 없습니다."
                    
            except Exception as e:
                print(f"Gemini API 오류: {e}")
                bot_response = "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
        
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
    