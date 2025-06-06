#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Function Calling 테스트 스크립트
"""

import sys
import os
import asyncio

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.chatbot_service import ChatbotService

async def test_function_calling():
    """Function Calling 테스트"""
    
    chatbot_service = ChatbotService()
    
    if not chatbot_service.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return
        
    test_messages = [
        "춘천 현재 날씨 어때?",
        "춘천 3시간 후 날씨",
        "노원 2시간 후 날씨 어떨까?",
        "서울 12시간 후 날씨",
        "춘천 종합 날씨 정보",
        "춘천 자세한 날씨",
    ]
    
    print("=== Gemini Function Calling 테스트 ===\n")
    
    for message in test_messages:
        print(f"입력: '{message}'")
        try:
            result = await chatbot_service.handle_weather_with_function_calling(message)
            print(f"응답: {result}")
        except Exception as e:
            print(f"오류: {e}")
        print("-" * 70)

if __name__ == "__main__":
    asyncio.run(test_function_calling())
