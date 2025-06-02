from typing import List, Dict, Any, Tuple
from datetime import datetime
from bisect import bisect_right

import aiohttp
from forecast.latlon_to_grid import latlon_to_grid

import os

# 단기 예보 발표 시각 이후 API 제공 시각 리스트. 1일 8회만 발표한다.
API_time_list = [210, 510, 810, 1110, 1410, 1710, 2010, 2310]

def get_base_time(currentDate: int, currentTime: int) -> Tuple[str, str]:
    """
    현재 날짜와 시각에 가장 근접한(직전) 기상청 예보 발표 기준 시각(base_time)과 
    해당 날짜(base_date)를 반환한다.

    Args:
        currentDate (int): 오늘 날짜(YYYYMMDD 형식의 8자리 정수).
        currentTime (int): 현재 시각(HHMM 형식의 4자리 정수).

    Returns:
        Tuple[str, str]:
            - baseDate (str): 기준 날짜(YYYYMMDD 형식).
            - baseTime (str): 기준 시각(HHMM 형식, 4자리).

    예외:
        기준 시각보다 이른 경우, 전날의 마지막 기준 시각(2300)과 전날 날짜를 반환한다.
    """
    idx = bisect_right(API_time_list, int(currentTime))

    # API 제공 시각들보다 이른 경우, currentDate에서 하루를 뺀 값, 시각 2300을 반환
    # 단, API 제공 시각은 02:10, 05:10, 08:10, 11:10, 14:10, 17:10, 20:10, 23:10이고, base_time 파라미터값으로 넣어줘야 하는 것은 매 시각 00분 단위이므로, 10를 빼고 반환한다.
    if idx == 0:
        return f"{currentDate-1:04d}", f"{API_time_list[-1] - 10:04d}"
    else:
        return f"{currentDate:04d}", f"{API_time_list[idx-1] - 10:04d}"
    

async def fetch_short_term_forecast(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    주어진 위도와 경도에 대해 기상청 단기예보(OpenAPI)에서 최신 예보 데이터를 조회하여,
    요청 코드(requestCode)와 예보 데이터(items)를 포함한 딕셔너리로 반환한다.

    Args:
        latitude (float): 조회할 위치의 위도 값.
        longitude (float): 조회할 위치의 경도 값.

    Returns:
        Dict[str, Any]: 
            - requestCode (str): 응답 코드(예: "200"은 성공, 그 외는 오류 코드).
            - items (List[Dict[str, Any]]): 예보 데이터 목록.
                각 데이터는 fcstDate, fcstTime, category, fcstValue 필드로 구성됨.
    
    예외:
        API 호출 실패 시 requestCode에 상태 코드가 담기며, items는 빈 리스트로 반환됨.
    """

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    
    serviceKey = os.getenv("KMA_SERVICE_KEY")

    # 기상청에서 예보를 발표하는 기준 시각을 입력으로 넣어야 하므로, 주어진 리스트에서 현재 시간에서 가깝고 직전인 시각을 선택한다.
    today = datetime.today()
    currentDate = today.strftime("%Y%m%d")
    currentTime = datetime.now().strftime("%H%M")
    baseDate, baseTime = get_base_time(int(currentDate), int(currentTime))

    print(baseDate, baseTime)

     # 해당 위도, 경도를 기상청 격자 좌표로 변경
    nx, ny = latlon_to_grid(latitude, longitude)

    params = {
        "serviceKey": serviceKey,
        "numOfRows": "100",
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": baseDate,
        "base_time": baseTime,
        "nx": nx,
        "ny": ny
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as response:
            if response.status == 200:
                response_json = await response.json()

                items = response_json.get("response", {}).get("body", {}).get("items", {}).get("item", [])
                result = [{
                         "fcstDate": item.get("fcstDate"),
                         "fcstTime": item.get("fcstTime"),
                         "category": item.get("category"),
                         "fcstValue": item.get("fcstValue")
                    } for item in items]

                return {
                        "requestCode": "200",
                        "items": result
                }
            
            else:
                return {
                        "requestCode": str(response.status),
                        "items": []
                    }