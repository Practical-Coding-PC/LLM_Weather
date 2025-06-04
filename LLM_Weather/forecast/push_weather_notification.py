import json
import sys
import os
import asyncio
import aiohttp

# forecast 폴더 기준 상위 디렉토리 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forecast.check_weather import check_weather
from kakaoapi.get_coordinates_by_city import get_coordinates_by_city
from repositories.user_repository import UserRepository
from repositories.notification_repository import NotificationRepository


async def push_weather_notification() -> None:
    """
    날씨 예보 정보를 기반으로 구독 중인 사용자들에게 푸시 알림을 전송하는 비동기 함수이다.

    사용자별로 저장된 알림 구독 정보와 위치 좌표를 바탕으로,
    6시간 이내에 비, 눈, 낙뢰, 강풍 등 주요 기상 현상이 예보된 경우,
    해당 내용을 자연어로 정리하여 웹 푸시 알림으로 전달한다.

    Returns:
        None
    """
    # 지역별로 지역별로 사람들을 분류한 dictionary. (예: {"서울": [user1, user2], "부산": [user3]})
    grouped_people_by_city = UserRepository.get_all()

    # 각 지역을 순회하며 해당 지역에 속한 사용자들에게 날씨 알림 전송
    for city_name, user_list in grouped_people_by_city.items():

        # 지역명 → 좌표(위도, 경도) 변환
        coordinates = await get_coordinates_by_city(city_name)
        latitude, longitude = coordinates['latitude'], coordinates['longitude']

        # 해당 좌표에 대해 6시간 이내 기상 예보 요약 메시지 생성
        message_summary = await check_weather(latitude, longitude)

        # 해당 지역 사용자에게 푸시 알림 전송
        for user_info in user_list:
            user_id_str = str(user_info['id'])

            # 사용자 ID로 알림 구독 정보 조회
            notification_info = NotificationRepository.get_by_user_id(user_id_str)[0]

            # 푸시 알림 전송을 위한 Web Push 키 정보 획득
            endpoint, p256dh_key, auth_key = notification_info['endpoint'], notification_info['p256dh_key'], notification_info['auth_key']

            # 푸시 알림을 전송할 외부 알림 서버 URL
            url = "http://localhost:3001/notify"

            # HTTP 요청 헤더
            headers = {
                "Content-Type": "application/json"
            }
            
            # 전송할 알림 데이터 구성
            data = json.dumps({
                "subscription": {
                    "endpoint": endpoint,
                    "p256dh_key": p256dh_key,
                    "auth_key": auth_key
                },
                "message": message_summary
            })

            # aiohttp를 이용해 비동기 POST 요청 전송
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    print("localhost:3001/notify로 전송완료!")
                    print(f"/Notify send Response Status Code: {response.status}")



if __name__ == "__main__":
    asyncio.run(push_weather_notification())