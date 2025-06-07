from datetime import datetime

class PromptBuilder:
    """챗봇용 프롬프트를 생성하는 클래스"""
    
    @staticmethod
    def build_function_call_prompt(user_message: str, conversation_history: str = "") -> str:
        """
        Function calling을 위한 프롬프트를 생성합니다.
        
        Args:
            user_message (str): 사용자 메시지
            conversation_history (str): 이전 대화 기록
            
        Returns:
            str: 생성된 프롬프트
        """
        # 현재 날짜와 시간 정보
        current_time = datetime.now()
        time_context = f"현재 시각: {current_time.strftime('%Y년 %m월 %d일 %H시 %M분')} ({current_time.strftime('%A')})"
        
        # 공통 함수 설명 및 조건
        common_instructions = f"""{time_context}

You are a weather and location information AI assistant. Analyze the user's question and call the appropriate function.

**Available Functions:**
- Use get_ultra_short_term_weather for current weather or short-term forecasts within 6 hours
- Use get_short_term_weather for forecasts from 7 hours to 5 days (120 hours)
- Use get_location_coordinates when you need latitude/longitude coordinates for a specific city or location
- Use get_cctv_info for CCTV, real-time road conditions, or traffic information
- If the user doesn't specify a location or uses expressions like '현재위치', '여기', '현재', use the current location by passing an empty string ("") for the location parameter
- If the question is not related to weather, location, or CCTV, answer directly without calling any function

**Important Rules:**
- When users ask about weather without specifying location (like "날씨 어때?", "비 와?"), pass an empty string ("") for the location parameter to use current location
- Interpret time expressions like "오늘", "내일", "모레" accurately based on current time
- When users use vague time expressions like "오전", "오후", "낮", "저녁", "밤", automatically choose appropriate specific times:
  * "오전" → 09:00
  * "오후" → 15:00  
  * "낮" → 12:00
  * "저녁" → 18:00
  * "밤" → 21:00
- Always call the appropriate function for weather-related queries
- Be helpful and use a friendly tone
- Provide concise and clear answers

Instructions:"""
        
        # 이전 대화가 있는 경우
        if conversation_history:
            return f"""
이전 대화:
{conversation_history}

사용자 질문: "{user_message}"

{common_instructions}
1. Consider the context of previous conversations for natural responses
2. Use helpful and friendly tone
3. Provide concise and clear answers
"""
        else:
            return f"""
사용자 질문: "{user_message}"

{common_instructions}
1. Use helpful and friendly tone
2. Provide concise and clear answers
"""
    
    @staticmethod
    def build_final_response_prompt(user_message: str, function_result: str) -> str:
        """
        Function call 결과를 바탕으로 최종 응답을 생성하기 위한 프롬프트를 생성합니다.
        
        Args:
            user_message (str): 사용자 메시지
            function_result (str): Function call 실행 결과
            
        Returns:
            str: 최종 응답 생성용 프롬프트
        """
        # 현재 날짜와 시간 정보 추가
        current_time = datetime.now()
        time_context = f"현재 시각: {current_time.strftime('%Y년 %m월 %d일 %H시 %M분')} ({current_time.strftime('%A')})"
        
        return f"""
{time_context}

사용자 질문: "{user_message}"
날씨 데이터: {function_result}

위 날씨 데이터를 바탕으로 사용자의 질문에 친근하고 간결하게 답변해주세요.
조건:
1. 기온, 날씨상태, 강수확률, 습도 등 주요 정보 포함
2. 간결하고 명확한 답변 (150자 이내)
3. 친근한 말투
4. 현재 시각을 고려하여 "오늘", "내일" 등의 표현을 정확히 해석
""" 