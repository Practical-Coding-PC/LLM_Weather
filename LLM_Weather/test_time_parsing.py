#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
날씨 챗봇 시간 표현 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from forecast.forecast_service import ForecastService

def test_time_expressions():
    """다양한 시간 표현 테스트"""
    
    forecast_service = ForecastService()
    
    test_messages = [
        "춘천 3시간 후 날씨 어때?",
        "춘천 3시간후 날씨",
        "춘천 3시간 뒤 날씨",
        "노원 2시간 후 날씨",
        "춘천 5시간 후",
        "서울 1시간 후 날씨는?",
        "춘천 날씨",  # 현재 날씨
        "춘천 내일 날씨",  # 미래 날씨
    ]
    
    print("=== 날씨 챗봇 시간 표현 분석 테스트 ===\n")
    
    for message in test_messages:
        print(f"입력: '{message}'")
        result = forecast_service.analyze_weather_request(message)
        print(f"결과: {result}")
        print("-" * 50)

if __name__ == "__main__":
    test_time_expressions()
