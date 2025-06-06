#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
기상청 API 연결 테스트 스크립트
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from chatbot.function_handler import WeatherFunctionHandler

async def test_api_connection():
    """API 연결 상태 테스트"""
    
    handler = WeatherFunctionHandler()
    
    print("=== 기상청 API 연결 테스트 ===")
    print(f"KMA_SERVICE_KEY 존재 여부: {'✅' if handler.KMA_SERVICE_KEY else '❌'}")
    if handler.KMA_SERVICE_KEY:
        print(f"API 키 길이: {len(handler.KMA_SERVICE_KEY)} 문자")
        print(f"API 키 앞 10자: {handler.KMA_SERVICE_KEY[:10]}...")
    
    print("\n=== 현재 날씨 API 테스트 ===")
    
    # 춘천 현재 날씨 테스트
    try:
        result = handler.get_current_weather("춘천")
        print("✅ 춘천 현재 날씨 성공!")
        print(f"결과: {result}")
    except Exception as e:
        print(f"❌ 춘천 현재 날씨 실패: {e}")
    
    print("\n=== 특정 시간 예보 API 테스트 ===")
    
    # 춘천 3시간 후 날씨 테스트
    try:
        result = handler.get_specific_hour_forecast("춘천", 3)
        print("✅ 춘천 3시간 후 날씨 성공!")
        print(f"결과: {result}")
    except Exception as e:
        print(f"❌ 춘천 3시간 후 날씨 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_connection())
