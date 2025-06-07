import os
import sys
import warnings
import google.generativeai as genai
from typing import Optional, Dict, Any, List

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from repositories.chat_repository import ChatRepository
from repositories.chat_message_repository import ChatMessageRepository

from chatbot.utils.cctv_utils import find_nearest_cctv
from chatbot.utils.weather_formatter import format_weather_data
from forecast.forecast_service import ForecastService
from kakaoapi.get_city_from_coordinates import get_city_from_coordinates
from kakaoapi.get_coordinates_by_city import get_coordinates_by_city

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
        
        # Function calling tools 정의
        self.weather_tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="get_ultra_short_term_weather",
                        description="1-6시간 이내의 초단기 날씨 예보 정보를 제공합니다. 현재 날씨부터 6시간까지의 상세한 기상 정보를 포함합니다.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "location": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="날씨를 알고 싶은 지역명 (예: 서울, 춘천, 노원, 효자동 등). '현재위치' 또는 '여기'라고 하면 사용자의 현재 위치를 사용합니다."
                                ),
                                "hours": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="몇 시간 후의 날씨를 알고 싶은지 (1-6시간, 기본값: 1)"
                                )
                            },
                            required=["location"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_short_term_weather",
                        description="7시간-5일(120시간) 이내의 단기 날씨 예보 정보를 제공합니다. 더 긴 기간의 날씨 예측 정보를 포함합니다.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "location": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="날씨를 알고 싶은 지역명 (예: 서울, 춘천, 노원, 효자동 등). '현재위치' 또는 '여기'라고 하면 사용자의 현재 위치를 사용합니다."
                                ),
                                "hours": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="몇 시간 후의 날씨를 알고 싶은지 (7-120시간, 기본값: 24)"
                                )
                            },
                            required=["location"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_location_coordinates",
                        description="도시나 지역명을 입력받아 해당 위치의 위도와 경도 좌표를 조회합니다. 카카오맵 API를 통해 정확한 좌표 정보를 제공합니다.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "city_name": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="좌표를 알고 싶은 도시나 지역명 (예: 원주, 춘천, 서울, 부산, 여수, 강남구, 종로구 등)"
                                )
                            },
                            required=["city_name"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_cctv_info",
                        description="특정 지역의 CCTV 정보를 제공합니다. 실시간 도로 상황이나 교통 상황을 확인할 수 있는 CCTV 카메라의 정보와 스트리밍 URL을 제공합니다.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "location": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="CCTV를 찾고 싶은 지역명 (예: 춘천, 효자동, 노원, 서울 등). 도로명이나 교차로명도 가능합니다."
                                )
                            },
                            required=["location"]
                        )
                    )
                ]
            )
        ]
        
        # Gemini 모델 초기화
        if self.GEMINI_API_KEY:
            genai.configure(api_key=self.GEMINI_API_KEY, transport="rest")
            self.model = genai.GenerativeModel(
                "models/gemini-1.5-flash-latest",
                tools=self.weather_tools
            )
        else:
            self.model = None

    async def _get_location_from_coords(self, latitude: float, longitude: float) -> str:
        """
        위도/경도로부터 지역명을 조회합니다.
        
        Args:
            latitude (float): 위도
            longitude (float): 경도
            
        Returns:
            str: 지역명
        """
        try:
            location = await get_city_from_coordinates(latitude, longitude)
            return location if location else "현재위치"
        except Exception as e:
            print(f"위치 조회 오류: {e}")
            return "현재위치"



    def _build_function_call_prompt(self, user_message: str, conversation_history: str = "") -> str:
        """
        Function calling을 위한 프롬프트를 생성합니다.
        
        Args:
            user_message (str): 사용자 메시지
            conversation_history (str): 이전 대화 기록
            
        Returns:
            str: 생성된 프롬프트
        """
        # 공통 함수 설명 및 조건
        common_instructions = """당신은 날씨 정보와 위치 정보를 제공하는 AI 어시스턴트입니다. 사용자의 질문을 분석하여 적절한 함수를 호출해주세요.

**사용 가능한 함수:**
- 현재 날씨나 6시간 이내의 단기 예보가 필요하면 get_ultra_short_term_weather 함수를 사용하세요
- 7시간 이후부터 5일(120시간) 이내의 예보가 필요하면 get_short_term_weather 함수를 사용하세요
- 특정 도시나 지역의 위도/경도 좌표 정보가 필요하면 get_location_coordinates 함수를 사용하세요
- CCTV, 실시간 도로 상황, 교통 상황을 확인하고 싶으면 get_cctv_info 함수를 사용하세요
- 사용자가 위치를 명시하지 않거나 '현재위치', '여기', '현재' 등으로 표현하면 현재 위치 정보를 활용하세요
- 날씨, 위치, CCTV와 관련이 없는 질문이면 함수를 호출하지 말고 직접 답변해주세요

**중요한 규칙:**
- 사용자가 단순히 "날씨 어때?", "비 와?" 등 위치를 명시하지 않고 날씨를 물어보면, location 파라미터를 빈 문자열("")로 전달하여 현재위치를 사용하도록 하세요

조건:"""
        
        # 이전 대화가 있는 경우
        if conversation_history:
            return f"""
이전 대화:
{conversation_history}

사용자 질문: "{user_message}"

{common_instructions}
1. 이전 대화의 맥락을 고려한 자연스러운 답변
2. 도움이 되고 친근한 말투
3. 간결하고 명확한 답변
"""
        else:
            return f"""
사용자 질문: "{user_message}"

{common_instructions}
1. 도움이 되고 친근한 말투
2. 간결하고 명확한 답변
"""

    async def _execute_function(self, function_name: str, args: Dict[str, Any], latitude: Optional[float] = None, longitude: Optional[float] = None) -> str:
        """
        Function calling으로 호출된 함수를 실행합니다.
        
        Args:
            function_name (str): 실행할 함수명
            args (dict): 함수 인자
            latitude (float, optional): 사용자의 현재 위치 좌표 위도
            longitude (float, optional): 사용자의 현재 위치 좌표 경도
            
        Returns:
            str: 함수 실행 결과
        """
        try:
            # 위치 조회 함수 처리
            if function_name == "get_location_coordinates":
                city_name = args.get("city_name", "")
                if not city_name:
                    return "도시명을 입력해주세요."
                
                coordinates = await get_coordinates_by_city(city_name)
                return f"{city_name}의 위치 정보:\n위도: {coordinates['latitude']:.6f}\n경도: {coordinates['longitude']:.6f}"
            
            # CCTV 정보 조회 함수 처리
            elif function_name == "get_cctv_info":
                location = args.get("location", "")
                if not location:
                    return "CCTV를 찾을 지역명을 입력해주세요."
                
                cctv_data = await find_nearest_cctv(location)
                
                if cctv_data:
                    return f"cctv_data:{cctv_data}"
                else:
                    return "해당 지역에서 CCTV를 찾을 수 없습니다."
            
            # 날씨 함수 처리
            elif function_name in ["get_ultra_short_term_weather", "get_short_term_weather"]:
                location = args.get("location", "")
                hours = args.get("hours", 1 if function_name == "get_ultra_short_term_weather" else 24)
                
                # 현재 위치 요청인지 확인 (명시적 키워드 또는 위치가 비어있는 경우)
                is_current_location = (
                    not location or  # 위치가 명시되지 않은 경우
                    location.lower() in ['현재위치', '여기', '현재', 'current', 'here']
                )
                
                if is_current_location and latitude and longitude:
                    # 현재 위치 사용
                    location_name = await self._get_location_from_coords(latitude, longitude)
                    lat, lon = latitude, longitude
                elif not location:
                    # 위치가 명시되지 않았지만 현재 위치 정보도 없는 경우 기본값 사용
                    location = "서울"
                    region_hit = self.forecast_service.find_coords_by_keyword(location)
                    if region_hit:
                        location_name = region_hit["name"]
                        lat, lon = region_hit["lat"], region_hit["lon"]
                    else:
                        return "위치 정보를 찾을 수 없습니다. 현재 위치를 허용하거나 구체적인 지역명을 입력해주세요."
                else:
                    # 지역명으로 좌표 검색
                    region_hit = self.forecast_service.find_coords_by_keyword(location)
                    if region_hit:
                        location_name = region_hit["name"]
                        lat, lon = region_hit["lat"], region_hit["lon"]
                    else:
                        # CSV에 없는 지역이면 카카오맵 API로 좌표 조회
                        try:
                            coordinates = await get_coordinates_by_city(location)
                            location_name = location
                            lat, lon = coordinates['latitude'], coordinates['longitude']
                        except Exception as e:
                            return f"{location}의 위치를 찾을 수 없습니다. 지원 지역: 춘천, 효자동, 노원, 서울 또는 정확한 도시명을 입력해주세요."
                
                # Function calling에 따라 적절한 메서드 호출
                if function_name == "get_ultra_short_term_weather":
                    weather_data = await self.forecast_service.get_ultra_short_term_forecast(lat, lon)
                    return format_weather_data(weather_data, location_name, "초단기", hours)
                else:
                    weather_data = await self.forecast_service.get_short_term_forecast(lat, lon)
                    return format_weather_data(weather_data, location_name, "단기", hours)
            
            else:
                return f"지원하지 않는 함수입니다: {function_name}"
                
        except Exception as e:
            return f"함수 실행 중 오류가 발생했습니다: {str(e)}"
    
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
            prompt = self._build_function_call_prompt(user_message, conversation_history)
            
            try:
                response = self.model.generate_content(prompt)
                
                # Function call이 있는지 확인
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            # Function call 실행
                            function_name = part.function_call.name
                            function_args = {}
                            for key, value in part.function_call.args.items():
                                function_args[key] = value
                            
                            # 함수 실행 (위치 정보 포함)
                            function_result = await self._execute_function(
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
                                final_prompt = f"""
사용자 질문: "{user_message}"
날씨 데이터: {function_result}

위 날씨 데이터를 바탕으로 사용자의 질문에 친근하고 간결하게 답변해주세요.
조건:
1. 기온, 날씨상태, 강수확률, 습도 등 주요 정보 포함
2. 간결하고 명확한 답변 (150자 이내)
3. 친근한 말투
"""
                                
                                final_response = self.model.generate_content(final_prompt)
                                bot_response = final_response.text.strip()
                            break
                    else:
                        # Function call이 없으면 일반 대화
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
    