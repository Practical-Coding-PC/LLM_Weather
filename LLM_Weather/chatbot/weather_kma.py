import requests
import json
from datetime import datetime, timedelta
from typing import Dict
import math
import pytz

# 춘천 하드코딩 좌표 (나중에 다른 파일에서 받을 예정)
DUMMY_CHUNCHEON_LAT = 37.8813
DUMMY_CHUNCHEON_LON = 127.7298

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간으로 현재 시간 반환"""
    return datetime.now(KST)

def convert_gps_to_grid(lat: float, lon: float) -> Dict[str, int]:
    """
    GPS 좌표(위도, 경도)를 기상청 격자 좌표(nx, ny)로 변환
    기상청에서 제공하는 좌표변환 공식 사용
    """
    # 기상청 격자 좌표계 상수
    RE = 6371.00877     # 지구 반경(km)
    GRID = 5.0          # 격자 간격(km)
    SLAT1 = 30.0        # 투영 위도1(degree)
    SLAT2 = 60.0        # 투영 위도2(degree)
    OLON = 126.0        # 기준점 경도(degree)
    OLAT = 38.0         # 기준점 위도(degree)
    XO = 43             # 기준점 X좌표(GRID)
    YO = 136            # 기준점 Y좌표(GRID)
    
    DEGRAD = math.pi / 180.0
    
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD
    
    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)
    
    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    
    x = ra * math.sin(theta) + XO
    y = ro - ra * math.cos(theta) + YO
    
    return {'nx': int(x + 0.5), 'ny': int(y + 0.5)}

# TODO: 나중에 다른 파일에서 GPS 좌표를 받아올 함수
# def get_gps_from_client():
#     """클라이언트에서 GPS 좌표를 받아오는 함수 (구현 예정)"""
#     # return {"latitude": lat, "longitude": lon}
#     pass

def get_current_location_coords():
    """현재 위치의 위도, 경도 반환 (현재는 춘천 하드코딩)"""
    # TODO: 나중에 get_gps_from_client() 함수로 교체
    return {
        "latitude": DUMMY_CHUNCHEON_LAT,
        "longitude": DUMMY_CHUNCHEON_LON,
        "location_name": "춘천시"
    }

def get_base_time() -> str:
    """현재 시간 기준으로 적절한 base_time 반환"""
    now = get_korean_time()
    
    # 초단기실황 base_time (매시 정각, 10분 이후 API 제공)
    if now.minute >= 10:
        return now.strftime('%H00')
    else:
        # 10분 전이면 이전 시간 사용
        prev_hour = now - timedelta(hours=1)
        return prev_hour.strftime('%H00')

def get_forecast_base_time() -> str:
    """초단기예보용 base_time 반환 (30분 단위, 45분 이후 API 제공)"""
    now = get_korean_time()
    
    # 45분 이후면 현재 시간의 30분 사용
    if now.minute >= 45:
        return now.strftime('%H30')
    # 15분 이후면 현재 시간의 00분 사용  
    elif now.minute >= 15:
        return now.strftime('%H00')
    else:
        # 15분 전이면 이전 시간의 30분 사용
        prev_hour = now - timedelta(hours=1)
        return prev_hour.strftime('%H30')

def parse_weather_category(category: str, value: str) -> str:
    """기상청 코드를 사람이 읽기 쉬운 형태로 변환"""
    
    # 하늘상태 (SKY)
    if category == 'SKY':
        sky_codes = {'1': '맑음', '3': '구름많음', '4': '흐림'}
        return sky_codes.get(value, f'하늘상태: {value}')
    
    # 강수형태 (PTY)
    elif category == 'PTY':
        pty_codes = {
            '0': '강수없음', '1': '비', '2': '비/눈', '3': '눈',
            '4': '소나기', '5': '빗방울', '6': '빗방울눈날림', '7': '눈날림'
        }
        return pty_codes.get(value, f'강수형태: {value}')
    
    # 기온 관련
    elif category in ['TMP', 'T1H']:
        return f'{value}°C'
    
    # 습도 (REH)
    elif category == 'REH':
        return f'습도 {value}%'
    
    # 강수확률 (POP)
    elif category == 'POP':
        return f'강수확률 {value}%'
    
    # 강수량 (RN1, PCP)
    elif category in ['RN1', 'PCP']:
        if value == '0' or value == '-' or not value:
            return '강수없음'
        return f'강수량 {value}mm'
    
    # 풍속 (WSD)
    elif category == 'WSD':
        return f'풍속 {value}m/s'
    
    # 풍향 (VEC)
    elif category == 'VEC':
        return f'풍향 {value}°'
    
    # 기타
    else:
        return f'{category}: {value}'

def get_current_weather(
        service_key: str | None = None,
        coords: tuple[float, float] | None = None
) -> str:
    """
    • service_key : 기상청 API 키 (필수)
    • coords      : (lat, lon) 형식의 위·경도 튜플.
                    None 이면 get_current_location_coords() 결과 사용
    """
    if not service_key:
        return "현재 위치의 날씨 정보를 가져올 수 없습니다. (API 키 없음)"

    # 1) 좌표·지역명 결정
    if coords:
        lat, lon = coords
        location_name = "선택한 위치"
    else:
        loc = get_current_location_coords()       # 춘천 하드코딩
        lat, lon = loc["latitude"], loc["longitude"]
        location_name = loc["location_name"]

    # 2) GPS → 기상청 격자 변환
    grid_coords = convert_gps_to_grid(lat, lon)

    base_date = get_korean_time().strftime("%Y%m%d")
    base_time = get_base_time()

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": service_key,
        "dataType": "JSON",
        "numOfRows": 10,
        "pageNo": 1,
        "base_date": base_date,
        "base_time": base_time,
        "nx": grid_coords["nx"],
        "ny": grid_coords["ny"],
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data["response"]["header"]["resultCode"] != "00":
            return f"{location_name}의 날씨 정보를 가져오는데 실패했습니다."

        items = data["response"]["body"]["items"]["item"]

        # 3) 필요한 값만 추림
        weather_data = {it["category"]: it["obsrValue"] for it in items}

        result = [f"{location_name} 현재 날씨:"]
        if "T1H" in weather_data:
            result.append(f"🌡️ 기온: {weather_data['T1H']}°C")
        if (pty := weather_data.get("PTY")) and pty != "0":
            result.append(f"🌧️ {parse_weather_category('PTY', pty)}")
        if (rn1 := weather_data.get("RN1")) and rn1 not in ("0", "-", ""):
            result.append(f"☔ {parse_weather_category('RN1', rn1)}")
        if "REH" in weather_data:
            result.append(f"💧 습도: {weather_data['REH']}%")
        if "WSD" in weather_data:
            result.append(f"💨 풍속: {weather_data['WSD']} m/s")

        return "\n".join(result)

    except requests.exceptions.RequestException as e:
        return f"{location_name}의 날씨 정보를 가져오는데 실패했습니다. (네트워크 오류: {e})"
    except (KeyError, TypeError) as e:
        return f"{location_name}의 날씨 정보를 파싱하는데 실패했습니다. (데이터 오류: {e})"

def get_comprehensive_weather(service_key: str = None) -> str:
    """현재 날씨 + 예보 정보 통합"""
    current = get_current_weather(service_key)
    forecast = get_forecast_weather(service_key, hours=3)  # 3시간만
    
    return f"{current}\n\n{forecast}"

def get_forecast_weather(
    service_key: str,
    hours: int = 3
) -> str:
    """
    초단기예보 정보를 가져옴 (최대 6시간)
    """
    loc = get_current_location_coords()
    lat, lon = loc["latitude"], loc["longitude"]
    location_name = loc["location_name"]

    if not service_key:
        return "예보 정보를 가져올 수 없습니다. (API 키 없음)"

    grid = convert_gps_to_grid(lat, lon)
    base_date = get_korean_time().strftime('%Y%m%d')
    base_time = get_forecast_base_time()

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
    params = {
        "serviceKey": service_key,
        "dataType": "JSON",
        "numOfRows": 60,  # 보통 6시간 * 10항목
        "pageNo": 1,
        "base_date": base_date,
        "base_time": base_time,
        "nx": grid["nx"],
        "ny": grid["ny"],
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data["response"]["header"]["resultCode"] != "00":
            return f"{location_name}의 예보 정보를 가져오는데 실패했습니다."

        items = data["response"]["body"]["items"]["item"]

        # 항목들을 시간순으로 정렬
        items_sorted = sorted(items, key=lambda x: x["fcstDate"] + x["fcstTime"])
        
        now = get_korean_time()
        target_times = [(now + timedelta(hours=i)).strftime('%H%M') for i in range(1, hours + 1)]

        forecast_texts = [f"{location_name} 향후 {hours}시간 예보:"]
        for hour in target_times:
            hour_data = [item for item in items_sorted if item["fcstTime"] == hour]
            if not hour_data:
                continue

            desc = f"{int(hour[:2])}시:"
            for item in hour_data:
                cat, val = item["category"], item["fcstValue"]
                if cat in ["PTY", "RN1", "REH", "TMP", "WSD"]:
                    desc += f" {parse_weather_category(cat, val)},"
            forecast_texts.append(desc.rstrip(","))

        return "\n".join(forecast_texts)

    except requests.exceptions.RequestException as e:
        return f"{location_name}의 예보 정보를 가져오는데 실패했습니다. (네트워크 오류: {e})"
    except Exception as e:
        return f"{location_name}의 예보 정보를 파싱하는 데 실패했습니다. (데이터 오류: {e})"
