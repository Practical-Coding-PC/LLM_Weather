from typing import Dict, List, Any
from dotenv import load_dotenv
from datetime import date

import aiohttp
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from forecast.latlon_to_grid import latlon_to_grid

async def fetch_ultra_short_term_forecast(latitude: float, longitude: float, baseTime: str)  -> List[Dict[str, Any]]:
    """
    Args:
    latitude (float): 위도.
    longitude (float): 경도.
    """

    load_dotenv()

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"

    serviceKey = os.getenv("SHORT_TERM_WEATHER_KEY")
    today = date.today()
    baseDate = today.strftime('%Y%m%d')
    
    # 해당 위도, 경도를 기상청 격자 좌표로 변경
    nx, ny = latlon_to_grid(latitude, longitude)

    print(nx, ny)

    params = {
        "serviceKey": serviceKey,
        "numOfRows": "100",
        "pageNo": "1",
        "dataType": "JSON",
        "base_date": baseDate,

        "base_time": baseTime,
        "nx": str(nx), # 위도
        "ny": str(ny) # 경도
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, params=params) as response:
                if response.status == 200:
                    response_json = await response.json()
                    result = [{
                         "fcstDate": item.get("fcstDate"),
                         "fcstTime": item.get("fcstTime"),
                         "category": item.get("category"),
                         "fcstValue": item.get("fcstValue")
                    } for item in response_json.get("response").get("body").get("items").get("item")]

                    return {
                         "requestCode": "200",
                         "items": result
                    }
                
                else:
                    return {
                        "requestCode": str(response.status),
                        "items": []
                    }

if __name__ == "__main__":
    get_ultra_short_term_forecast(37.9231472222222, 127.748363888888, "0630")