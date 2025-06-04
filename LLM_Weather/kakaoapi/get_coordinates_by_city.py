from dotenv import load_dotenv

import os
import aiohttp
import asyncio

async def get_coordinates_by_city(city_name: str) -> dict:
    """
    카카오맵 REST API를 사용하여 시 이름으로 좌표(위도, 경도값)를 가져옵니다.

    Args:
        city_name (str): 시 이름. ex) 원주, 춘천, 서울, 부산, 여수

    Returns:
        dict: 좌표 정보를 담은 딕셔너리로, 다음과 같은 형식입니다:
              {
                  "latitude": float,   # 위도
                  "longitude": float   # 경도
              }
    """

    url = "https://dapi.kakao.com/v2/local/search/address.json"
    params = {
        'query': city_name
    }

    headers = {
        'Authorization': f"KakaoAK {os.environ.get('KAKAO_REST_API_KEY')}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params, headers=headers) as response:
            print(f"KakaoMap Response Status Code(좌표로 변환): {response.status}")

            json_response = await response.json()
            
            document = json_response.get('documents')[0]

            # Y 좌표값 (=위도, latitude)
            latitude = float(document['y'])

            # X 좌표값 (= 경도, longitude)
            longitude = float(document['x'])

            return {'latitude': latitude, 'longitude': longitude}


if __name__ == "__main__":
    load_dotenv()
    print(asyncio.run(get_coordinates_by_city("원주")))

