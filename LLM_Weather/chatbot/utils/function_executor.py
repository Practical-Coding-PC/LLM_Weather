import os
import sys
from typing import Dict, Any, Optional

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chatbot.utils.cctv_utils import find_nearest_cctv
from chatbot.utils.weather_formatter import format_weather_data
from chatbot.utils.location_handler import LocationHandler


class FunctionExecutor:
    """Function calling으로 호출된 함수들을 실행하는 클래스"""
    
    def __init__(self, forecast_service):
        """
        FunctionExecutor 초기화
        
        Args:
            forecast_service: ForecastService 인스턴스
        """
        self.forecast_service = forecast_service
    
    async def execute_function(
        self, 
        function_name: str, 
        args: Dict[str, Any], 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None
    ) -> str:
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
            if function_name == "get_cctv_info":
                return await self._execute_cctv_info(args)
            elif function_name in ["get_ultra_short_term_weather", "get_short_term_weather"]:
                return await self._execute_weather_function(function_name, args, latitude, longitude)
            else:
                return f"지원하지 않는 함수입니다: {function_name}"
                
        except Exception as e:
            return f"함수 실행 중 오류가 발생했습니다: {str(e)}"
    
    async def _execute_cctv_info(self, args: Dict[str, Any]) -> str:
        """CCTV 정보 조회 함수를 실행합니다."""
        location = args.get("location", "")
        if not location:
            return "CCTV를 찾을 지역명을 입력해주세요."
        
        cctv_data = await find_nearest_cctv(location)
        
        if cctv_data:
            return f"cctv_data:{cctv_data}"
        else:
            return "해당 지역에서 CCTV를 찾을 수 없습니다."
    
    async def _execute_weather_function(
        self, 
        function_name: str, 
        args: Dict[str, Any], 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None
    ) -> str:
        """날씨 조회 함수를 실행합니다."""
        location = args.get("location", "")
        hours = args.get("hours", 1 if function_name == "get_ultra_short_term_weather" else 24)
        
        # 하루 전체 날씨 요청인지 확인
        full_day_keywords = ["하루", "전체", "종일", "오늘 날씨", "내일 날씨", "24시간", "하루종일", "전체적으로"]
        full_day = args.get("full_day", False) or any(keyword in location for keyword in full_day_keywords)
        
        # 위치 정보 해결
        try:
            location_info = await LocationHandler.resolve_location(
                location, latitude, longitude, self.forecast_service
            )
        except ValueError as e:
            print(f"location ValueError: {str(e)}")
            return str(e)
        except Exception as e:
            print(f"location 예상치 못한 오류: {str(e)}")
            return f"위치 처리 중 오류가 발생했습니다: {str(e)}"
        
        lat, lon = location_info["lat"], location_info["lon"]

        # Function calling에 따라 적절한 메서드 호출
        if function_name == "get_ultra_short_term_weather":
            weather_data = await self.forecast_service.get_ultra_short_term_forecast(lat, lon)
            formatted_data = format_weather_data(weather_data, location, "초단기", hours, full_day)
        else:
            weather_data = await self.forecast_service.get_short_term_forecast(lat, lon)
            formatted_data = format_weather_data(weather_data, location, "단기", hours, full_day) 

        print(formatted_data)
        return formatted_data