from dotenv import load_dotenv

import os
import aiohttp

async def get_city_from_coordinates(latitude: float, longitude: float) -> str:
    """
    카카오맵 REST API를 사용하여 좌표로부터 행정구역(시) 이름을 가져옵니다.

    Args:
        latitude (float): 위도 값.
        longitude (float): 경도 값.

    Returns:
        str: 변환된 행정구역(시)의 이름입니다. API 호출에 실패하거나 해당 좌표의
             행정구역 정보를 찾을 수 없는 경우, 빈 문자열("")이나 None을 반환할 수 있습니다.
    """

    load_dotenv()

    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode"
    params = {
        "x": str(longitude),
        "y": str(latitude)
    }

    headers = {
        "Authorization": f"KakaoAK {os.environ.get('KAKAO_REST_API_KEY')}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:

            print(f"KakaoMap Response Status Code(행정구역명으로 변환): {response.status}")
            
            json_response = await response.json()

            print(json_response.get('documents')[0])

            document = json_response.get('documents')[0]

            location = document.get('region_2depth_name')

            # 'region_2depth_name'(구 단위)이 비어있을 경우, 'region_1depth_name'(시도 단위)로 대체한다. ex) 세종특별자치시
            if location == '':
                location = document.get('region_1depth_name')
            

            # 시로 끝나는 경우 시를 제거한다.
            if location.endswith("시"):
                location = location.removesuffix("시")
            # 군으로 끝나는 경우 군을 제거한다.
            elif location.endswith("군"):
                location = location.removesuffix("군")
            # 구로 끝나는 경우 구를 제거한다.
            elif location.endswith("구"):
                location = location.removesuffix("구")
            
            return location