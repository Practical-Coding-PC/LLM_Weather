import asyncio
from datetime import datetime
import sys
import os
import math

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.utils.ultra_short_term_forecast import fetch_ultra_short_term_forecast

def summarize_weather(alerts: dict) -> str:
    """
    주어진 기상 예보 정보를 바탕으로,
    예상 시점에 따라 자연스러운 메시지를 생성하여 한 줄로 요약합니다.

    Args:
        alerts (dict): 예보 항목별(강수, 낙뢰, 강풍)로 발생 예상 시간(hour)이 담긴 딕셔너리.
                       예: {"rain": 1, "lightning": 3, "strong_wind": None}

    Returns:
        str: 사용자에게 보여줄 자연어 요약 메시지.
             예: "곧 비나 눈이 올 수 있어요 ☔ / 조만간 낙뢰가 있을 수 있어요 ⚡ — 외출 시 주의하세요!"
    """
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


async def check_weather(latitude: float, longitude: float) -> str:
    """
    주어진 위도와 경도를 기준으로 초단기 예보 데이터를 분석하여,
    향후 6시간 이내에 비, 눈, 낙뢰, 강풍 등 주요 기상 요소가 발생할 가능성을 판단하고,
    사용자에게 전달할 자연어 요약 메시지를 반환합니다.

    Args:
        latitude (float): 위도 좌표.
        longitude (float): 경도 좌표.

    Returns:
        str: 요약된 자연어 메시지. 예: "곧 비나 눈이 올 수 있어요 ☔ / 조만간 낙뢰가 있을 수 있어요 ⚡ — 외출 시 주의하세요!"
    """
    # 기상 상태별 최초 예보 시각(시간 단위)을 담기 위한 딕셔너리
    alerts = {
        "rain": None,         # 비나 눈 예보 시점
        "lightning": None,    # 낙뢰 예보 시점
        "strong_wind": None,  # 풍속 6.0m/s 이상 예보 시점
        "message": ""
    }

    now = datetime.now()

    # 예보 데이터 호출
    result = await fetch_ultra_short_term_forecast(latitude, longitude)
    items = result.get('items', [])

    for item in items:
        category = item['category'] # category
        fcstValue = item['fcstValue'] # fcstValue

        # 예보 시각 계산
        fcst_dt = datetime.strptime(item['fcstDate'] + item['fcstTime'], "%Y%m%d%H%M")
        # (예보 시각 - 현재 시각) 값을 올림 처리
        hours = math.ceil((fcst_dt - now).total_seconds() / 3600)

        if hours < 0 or hours > 6:
            continue  # 6시간 이내만 분석

        # 강수(PTY): 비/눈/소나기 예보
        if category == "PTY" and fcstValue != "0" and alerts['rain'] is None:
            alerts['rain'] = hours

        # 낙뢰(LGT)
        elif category == "LGT" and fcstValue != "0" and alerts['lightning'] is None:
            alerts['lightning'] = hours

        # 풍속(WSD): 6.0m/s 이상이면 강풍
        elif category == "WSD":
            wind_speed = float(fcstValue)
            if wind_speed >= 6.0 and alerts["strong_wind"] is None:
                alerts['strong_wind'] = hours

    # 자연어 메시지 생성
    message_summary = summarize_weather(alerts)
    return message_summary


if __name__ == "__main__":
    print(asyncio.run(check_weather(37.863770, 127.757174)))