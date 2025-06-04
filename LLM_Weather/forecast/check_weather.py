import asyncio
from datetime import datetime, timedelta
import sys
import os
import math

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.ultra_short_term_forecast import fetch_ultra_short_term_forecast


# 샘플 데이터
now = datetime.now()
base_date = datetime.now().strftime("%Y%m%d")

def make_fcst_time(hour_offset):
    return (now + timedelta(hours=hour_offset)).strftime("%H%M")

items = [
    # 비 (PTY: 1=비)
    {"fcstDate": base_date, "fcstTime": make_fcst_time(1), "category": "PTY", "fcstValue": "1"},
    # 눈 (PTY: 3=눈)
    {"fcstDate": base_date, "fcstTime": make_fcst_time(2), "category": "PTY", "fcstValue": "3"},
    # 낙뢰 (LGT: 1~3)
    {"fcstDate": base_date, "fcstTime": make_fcst_time(3), "category": "LGT", "fcstValue": "1"},
    # 강풍 (WSD: 6.0 이상)
    {"fcstDate": base_date, "fcstTime": make_fcst_time(4), "category": "WSD", "fcstValue": "6.3"},

    # 기타 날씨 항목 (온도/하늘상태 등)
    {"fcstDate": base_date, "fcstTime": make_fcst_time(1), "category": "T1H", "fcstValue": "22"},
    {"fcstDate": base_date, "fcstTime": make_fcst_time(2), "category": "REH", "fcstValue": "60"},
    {"fcstDate": base_date, "fcstTime": make_fcst_time(3), "category": "SKY", "fcstValue": "4"},
]

def summarize_weather(alerts: dict) -> str:
    message_summary = []

    def phrase(hour, description, emoji):
        if hour <= 1:
            return f"곧 {description} {emoji}"
        elif hour <= 3:
            return f"조만간 {description} {emoji}"
        else:
            return f"오늘 안에 {description} {emoji}"

    if alerts.get("rain") is not None:
        message_summary.append(phrase(alerts["rain"], "비나 눈이 올 수 있어요", "☔"))

    if alerts.get("lightning") is not None:
        message_summary.append(phrase(alerts["lightning"], "낙뢰가 있을 수 있어요", "⚡"))

    if alerts.get("strong_wind") is not None:
        message_summary.append(phrase(alerts["strong_wind"], "바람이 강하게 불 수 있어요", "💨"))

    if message_summary:
        return " / ".join(message_summary) + " — 외출 시 주의하세요!"
    else:
        return "☀️ 현재 6시간 내에 뚜렷한 기상 특이사항은 없습니다."

async def check_weather(latitude: float, longitude: float):
    """
    지정한 위도 및 경도 좌표에 대해 향후 6시간의 초단기 예보 데이터를 가져와서,
    강수, 낙뢰, 강풍 등의 주요 기상 요소를 분석하여 알림 정보를 반환한다.

    Args:
        latitude (float): 위도 좌표.
        longitude (float): 경도 좌표.

    Returns:
        dict: 알림 대상이 되는 기상 조건 및 메시지가 포함된 사전.
              예: {'rain': True, 'lightning': False, 'message': '우산을 챙기세요! 비 예보 있음'}
    """
    # 강수 메시지를 작성하기 위한 dictionary. value로 True 값을 가지면, 해당 예보가 예정됨을 나타낸다.
    alerts = {
        "rain": None,
        "lightning": None,
        "strong_wind": None,
        "message": ""
    }

    # 현재 시간
    now = datetime.now()

    # result = await fetch_ultra_short_term_forecast(latitude, longitude)
    # items = result.get('items', [])
    
    for item in items:
        category = item['category']
        fcstValue = item['fcstValue']

        fcst_dt = datetime.strptime(item['fcstDate'] + item['fcstTime'], "%Y%m%d%H%M")
        hours = math.ceil((fcst_dt - now).total_seconds() / 3600)

        if hours < 0 or hours > 6:
            continue # 과거나 6시간 이후는 무시
        
        # 강수 현황 판단
        if category == "PTY" and fcstValue != "0" and alerts['rain'] is None:
            alerts['rain'] = hours
        # 낙뢰 현황 판단
        elif category == "LGT" and fcstValue != "0" and alerts['lightning'] is None:
            alerts['lightning'] = hours
        elif category == "WSD":
            wind_speed = float(fcstValue)

            if wind_speed >= 6.0 and alerts["strong_wind"] is None:
                alerts['strong_wind'] = hours

        
    # 자연어 메시지 생성
    message_summary = summarize_weather(alerts)

    return message_summary


if __name__ == "__main__":
    print(asyncio.run(check_weather(37.863770, 127.757174)))