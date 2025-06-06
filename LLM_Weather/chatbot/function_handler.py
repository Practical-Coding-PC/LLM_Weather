import os
import json
from typing import Dict, Any, Optional

# 날씨 함수들 import
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.utils.weather_kma import (
    get_current_weather as kma_get_current_weather,
    get_specific_hour_forecast as kma_get_specific_hour_forecast, 
    get_short_term_forecast as kma_get_short_term_forecast,
    get_comprehensive_weather as kma_get_comprehensive_weather,
    get_coordinates_for_weather
)

class WeatherFunctionHandler:
    """
    Gemini Function Calling을 위한 날씨 함수 핸들러
    """
    
    def __init__(self):
        self.KMA_SERVICE_KEY = os.getenv('KMA_SERVICE_KEY')
    
    def get_current_weather(self, location: str) -> str:
        """현재 날씨 조회"""
        if not self.KMA_SERVICE_KEY:
            return f"{location}의 날씨 정보를 가져올 수 없습니다. (API 키 없음)"
        
        try:
            print(f"🔄 get_current_weather 호출: location={location}")
            result = kma_get_current_weather(
                service_key=self.KMA_SERVICE_KEY,
                location=location
            )
            print(f"✅ get_current_weather 성공: {len(result)} 문자")
            return result
        except Exception as e:
            error_msg = f"{location}의 현재 날씨 조회 중 오류가 발생했습니다: {str(e)}"
            print(f"❌ get_current_weather 오류: {error_msg}")
            print(f"❌ 전체 예외: {repr(e)}")
            return error_msg
    
    def get_specific_hour_forecast(self, location: str, hours: int) -> str:
        """특정 시간 후 날씨 조회"""
        if not self.KMA_SERVICE_KEY:
            return f"{location}의 예보 정보를 가져올 수 없습니다. (API 키 없음)"
        
        if hours < 1 or hours > 6:
            return "1-6시간 범위의 예보만 조회할 수 있습니다."
        
        try:
            print(f"🔄 get_specific_hour_forecast 호출: location={location}, hours={hours}")
            result = kma_get_specific_hour_forecast(
                service_key=self.KMA_SERVICE_KEY,
                hours=hours,
                location=location
            )
            print(f"✅ get_specific_hour_forecast 성공: {len(result)} 문자")
            return result
        except Exception as e:
            error_msg = f"{location}의 {hours}시간 후 예보 조회 중 오류가 발생했습니다: {str(e)}"
            print(f"❌ get_specific_hour_forecast 오류: {error_msg}")
            return error_msg
    
    def get_short_term_forecast(self, location: str, hours: int) -> str:
        """장기 예보 조회"""
        if not self.KMA_SERVICE_KEY:
            return f"{location}의 예보 정보를 가져올 수 없습니다. (API 키 없음)"
        
        if hours < 7 or hours > 120:
            return "7-120시간 범위의 예보만 조회할 수 있습니다."
        
        try:
            return kma_get_short_term_forecast(
                service_key=self.KMA_SERVICE_KEY,
                hours=hours,
                location=location
            )
        except Exception as e:
            return f"{location}의 {hours}시간 후 예보 조회 중 오류가 발생했습니다: {str(e)}"
    
    def get_comprehensive_weather(self, location: str) -> str:
        """종합 날씨 정보 조회"""
        if not self.KMA_SERVICE_KEY:
            return f"{location}의 날씨 정보를 가져올 수 없습니다. (API 키 없음)"
        
        try:
            return kma_get_comprehensive_weather(
                service_key=self.KMA_SERVICE_KEY,
                location=location
            )
        except Exception as e:
            return f"{location}의 종합 날씨 조회 중 오류가 발생했습니다: {str(e)}"
    
    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """
        함수 이름과 인자를 받아서 해당 함수를 실행합니다
        """
        print(f"🔧 Function Call: {function_name}({arguments})")
        
        if function_name == "get_current_weather":
            return self.get_current_weather(arguments.get("location", "춘천"))
        
        elif function_name == "get_specific_hour_forecast":
            return self.get_specific_hour_forecast(
                location=arguments.get("location", "춘천"),
                hours=arguments.get("hours", 3)
            )
        
        elif function_name == "get_short_term_forecast":
            return self.get_short_term_forecast(
                location=arguments.get("location", "춘천"),
                hours=arguments.get("hours", 12)
            )
        
        elif function_name == "get_comprehensive_weather":
            return self.get_comprehensive_weather(arguments.get("location", "춘천"))
        
        else:
            return f"알 수 없는 함수입니다: {function_name}"
