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
from forecast.forecast_service import ForecastService
from forecast.utils.ultra_short_term_forecast import fetch_ultra_short_term_forecast
from forecast.utils.short_term_forecast import fetch_short_term_forecast
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

    def _format_weather_data(self, weather_data: Dict[str, Any], location_name: str, forecast_type: str = "단기", target_hours: int = 0) -> str:
        """
        기상청 API에서 받은 원시 데이터를 사용자 친화적인 형태로 변환합니다.
        
        Args:
            weather_data (Dict[str, Any]): 기상청 API 응답 데이터
            location_name (str): 지역명
            forecast_type (str): 예보 타입 ("초단기" 또는 "단기")
            target_hours (int): 몇 시간 후의 데이터를 원하는지 (0이면 가장 가까운 시간)
            
        Returns:
            str: 포맷된 날씨 정보
        """
        if weather_data.get("requestCode") != "200":
            return f"{location_name}의 날씨 정보를 가져오는데 실패했습니다."
        
        items = weather_data.get("items", [])
        if not items:
            return f"{location_name}의 날씨 데이터가 없습니다."
        
        # 시간별로 데이터 그룹화
        time_groups = {}
        for item in items:
            date_time = f"{item['fcstDate']}_{item['fcstTime']}"
            if date_time not in time_groups:
                time_groups[date_time] = {}
            time_groups[date_time][item['category']] = item['fcstValue']
        
        # 적절한 시간대의 데이터 선택
        if not time_groups:
            return f"{location_name}의 날씨 데이터를 처리할 수 없습니다."
        
        sorted_times = sorted(time_groups.keys())
        
        if target_hours == 0:
            # 가장 가까운 시간대
            selected_time = sorted_times[0]
        else:
            # 현재 시간 + target_hours에 해당하는 시간대 찾기
            from datetime import datetime, timedelta
            current_time = datetime.now()
            target_time = current_time + timedelta(hours=target_hours)
            target_date_str = target_time.strftime("%Y%m%d")
            target_hour_str = target_time.strftime("%H00")
            target_time_key = f"{target_date_str}_{target_hour_str}"
            
            # 정확한 시간이 있으면 사용, 없으면 가장 가까운 시간 사용
            if target_time_key in time_groups:
                selected_time = target_time_key
            else:
                # 가장 가까운 시간 찾기
                selected_time = sorted_times[0]
                for time_key in sorted_times:
                    if time_key >= target_time_key:
                        selected_time = time_key
                        break
        
        forecast_data = time_groups[selected_time]
        
        # 시간 정보 파싱
        date_str = selected_time.split('_')[0]
        time_str = selected_time.split('_')[1]
        formatted_date = f"{date_str[4:6]}월 {date_str[6:8]}일"
        formatted_time = f"{time_str[:2]}시"
        
        result_parts = [f"{location_name} {forecast_type} 예보 ({formatted_date} {formatted_time}):"]
        
        # 기온 (TMP)
        if "TMP" in forecast_data:
            result_parts.append(f"🌡️ 기온: {forecast_data['TMP']}°C")
        
        # 하늘상태 (SKY)
        if "SKY" in forecast_data:
            sky_value = forecast_data['SKY']
            if sky_value == "1":
                sky_desc = "맑음"
            elif sky_value == "3":
                sky_desc = "구름많음"
            elif sky_value == "4":
                sky_desc = "흐림"
            else:
                sky_desc = f"하늘상태: {sky_value}"
            result_parts.append(f"☁️ {sky_desc}")
        
        # 강수형태 (PTY)
        if "PTY" in forecast_data and forecast_data['PTY'] != "0":
            pty_value = forecast_data['PTY']
            if pty_value == "1":
                pty_desc = "비"
            elif pty_value == "2":
                pty_desc = "비/눈"
            elif pty_value == "3":
                pty_desc = "눈"
            elif pty_value == "4":
                pty_desc = "소나기"
            else:
                pty_desc = f"강수형태: {pty_value}"
            result_parts.append(f"🌧️ {pty_desc}")
        
        # 강수확률 (POP)
        if "POP" in forecast_data:
            result_parts.append(f"☔ 강수확률: {forecast_data['POP']}%")
        
        # 습도 (REH)
        if "REH" in forecast_data:
            result_parts.append(f"💨 습도: {forecast_data['REH']}%")
        
        # 풍속 (WSD)
        if "WSD" in forecast_data:
            result_parts.append(f"🌬️ 풍속: {forecast_data['WSD']} m/s")
        
        return "\n".join(result_parts)

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
            
            # 날씨 함수 처리
            elif function_name in ["get_ultra_short_term_weather", "get_short_term_weather"]:
                location = args.get("location", "서울")
                hours = args.get("hours", 1 if function_name == "get_ultra_short_term_weather" else 24)
                
                # 현재 위치 요청인지 확인
                is_current_location = location.lower() in ['현재위치', '여기', '현재', 'current', 'here']
                
                if is_current_location and latitude and longitude:
                    # 현재 위치 사용
                    location_name = await self._get_location_from_coords(latitude, longitude)
                    lat, lon = latitude, longitude
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
                    weather_data = await fetch_ultra_short_term_forecast(lat, lon)
                    return self._format_weather_data(weather_data, location_name, "초단기", hours)
                else:  # get_short_term_weather
                    weather_data = await fetch_short_term_forecast(lat, lon)
                    return self._format_weather_data(weather_data, location_name, "단기", hours)
            
            else:
                return f"지원하지 않는 함수입니다: {function_name}"
                
        except Exception as e:
            return f"함수 실행 중 오류가 발생했습니다: {str(e)}"

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
        
        # 현재 위치 컨텍스트 생성
        location_context = ""
        if latitude and longitude:
            try:
                current_location = await self._get_location_from_coords(
                    latitude, 
                    longitude
                )
                location_context = f"\n\n[사용자 현재 위치 정보: {current_location} (위도: {latitude:.4f}, 경도: {longitude:.4f})]"
            except Exception as e:
                print(f"위치 정보 처리 오류: {e}")
        
        # Gemini API가 설정되지 않은 경우 기본 응답
        if not self.GEMINI_API_KEY:
            bot_response = await self.get_default_response(user_message)
        else:
            # CCTV 관련 키워드 확인 (기존 로직 유지)
            cctv_keywords = ['cctv', 'CCTV', '씨씨티비', '캠', '카메라', '도로', '교통', '실시간']
            is_cctv_related = any(keyword in user_message for keyword in cctv_keywords)
            
            if is_cctv_related:
                # CCTV 요청 처리
                bot_response = await self.get_cctv_info(user_message)
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
                
                # Function calling을 위한 프롬프트
                if conversation_history:
                    prompt = f"""
이전 대화:
{conversation_history}

사용자 질문: "{user_message}"{location_context}

당신은 날씨 정보와 위치 정보를 제공하는 AI 어시스턴트입니다. 사용자의 질문을 분석하여 적절한 함수를 호출해주세요.

**사용 가능한 함수:**
- 현재 날씨나 6시간 이내의 단기 예보가 필요하면 get_ultra_short_term_weather 함수를 사용하세요
- 7시간 이후부터 5일(120시간) 이내의 예보가 필요하면 get_short_term_weather 함수를 사용하세요
- 특정 도시나 지역의 위도/경도 좌표 정보가 필요하면 get_location_coordinates 함수를 사용하세요
- 사용자가 '현재위치', '여기', '현재' 등으로 표현하면 현재 위치 정보를 활용하세요
- 날씨나 위치와 관련이 없는 질문이면 함수를 호출하지 말고 직접 답변해주세요

조건:
1. 이전 대화의 맥락을 고려한 자연스러운 답변
2. 도움이 되고 친근한 말투
3. 간결하고 명확한 답변
"""
                else:
                    prompt = f"""
사용자 질문: "{user_message}"{location_context}

당신은 날씨 정보와 위치 정보를 제공하는 AI 어시스턴트입니다. 사용자의 질문을 분석하여 적절한 함수를 호출해주세요.

**사용 가능한 함수:**
- 현재 날씨나 6시간 이내의 단기 예보가 필요하면 get_ultra_short_term_weather 함수를 사용하세요
- 7시간 이후부터 5일(120시간) 이내의 예보가 필요하면 get_short_term_weather 함수를 사용하세요
- 특정 도시나 지역의 위도/경도 좌표 정보가 필요하면 get_location_coordinates 함수를 사용하세요
- 사용자가 '현재위치', '여기', '현재' 등으로 표현하면 현재 위치 정보를 활용하세요
- 날씨나 위치와 관련이 없는 질문이면 함수를 호출하지 말고 직접 답변해주세요

조건:
1. 도움이 되고 친근한 말투
2. 간결하고 명확한 답변
"""
                
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
                                if function_name == "get_location_coordinates":
                                    # 위치 조회 함수의 경우 직접 결과를 반환
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
    
 