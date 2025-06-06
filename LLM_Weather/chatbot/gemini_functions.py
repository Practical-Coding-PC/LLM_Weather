import google.generativeai as genai
from typing import Dict, Any, List

def define_weather_functions() -> List[Dict[str, Any]]:
    """
    Gemini Function Calling을 위한 날씨 함수들 정의
    """
    
    functions = [
        {
            "name": "get_current_weather",
            "description": "현재 날씨 정보를 조회합니다",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "location": {
                        "type": "STRING",
                        "description": "날씨를 조회할 지역명 (예: 춘천, 노원, 서울)"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "name": "get_specific_hour_forecast",
            "description": "특정 시간 후의 날씨 예보를 조회합니다",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "location": {
                        "type": "STRING",
                        "description": "날씨를 조회할 지역명 (예: 춘천, 노원, 서울)"
                    },
                    "hours": {
                        "type": "INTEGER",
                        "description": "몇 시간 후의 날씨인지 (1-6시간)"
                    }
                },
                "required": ["location", "hours"]
            }
        },
        {
            "name": "get_short_term_forecast",
            "description": "장기 날씨 예보를 조회합니다 (6시간 초과~5일)",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "location": {
                        "type": "STRING",
                        "description": "날씨를 조회할 지역명 (예: 춘천, 노원, 서울)"
                    },
                    "hours": {
                        "type": "INTEGER",
                        "description": "몇 시간 후의 날씨인지 (7-120시간)"
                    }
                },
                "required": ["location", "hours"]
            }
        },
        {
            "name": "get_comprehensive_weather",
            "description": "현재 날씨부터 장기 예보까지 종합적인 날씨 정보를 조회합니다",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "location": {
                        "type": "STRING",
                        "description": "날씨를 조회할 지역명 (예: 춘천, 노원, 서울)"
                    }
                },
                "required": ["location"]
            }
        }
    ]
    
    return functions

def create_function_calling_model(api_key: str):
    """
    Function Calling이 가능한 Gemini 모델을 생성합니다
    """
    genai.configure(api_key=api_key, transport="rest")
    
    functions = define_weather_functions()
    
    model = genai.GenerativeModel(
        "models/gemini-1.5-flash-latest",
        tools=functions
    )
    
    return model
