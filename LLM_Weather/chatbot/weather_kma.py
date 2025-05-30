import requests
import json
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import pytz

# CSV 파일 경로
CSV_PATH = os.path.join(os.path.dirname(__file__), "초단기예보-춘천-노원-csv.csv")

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간으로 현재 시간 반환"""
    return datetime.now(KST)

def load_region_data():
    """CSV 파일에서 지역 데이터 로드"""
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8")
        return df
    except Exception as e:
        print(f"CSV 파일 로딩 오류: {e}")
        return None

def convert_coord_to_decimal(coord_value):
    """
    경도(초/100), 위도(초/100) 값을 도 단위로 변환
    - 도 단위(0~200)면 그대로 반환
    - 초/100 단위면 3600으로 나눠 도로 환산
    """
    if pd.isna(coord_value):
        return None
    
    # 도 단위(일반적으로 0~200 범위)면 그대로 반환
    if coord_value < 200:
        return float(coord_value)
    
    # 초/100 단위면 도 단위로 변환 (초 → 도: /3600, /100: *100이므로 /360000)
    return float(coord_value) / 360000

def find_coordinates_by_region(region_name: str) -> Optional[Dict]:
    """
    지역명으로 CSV에서 좌표와 격자 정보를 찾기
    1단계, 2단계, 3단계 순서로 검색
    """
    df = load_region_data()
    if df is None:
        return None
    
    # 키워드 매핑 (기존 REGION_KEYWORDS 활용)
    region_keywords = {
        "서울": ["서울특별시"],
        "춘천": ["춘천시"],
        "노원": ["노원구"],
        "효자동": ["효자1동", "효자2동", "효자3동"],
        "효자": ["효자1동"],
        "월계동": ["월계1동", "월계2동", "월계3동"],
        "중계동": ["중계본동", "중계1동", "중계2.3동", "중계4동"],
        "상계동": ["상계1동", "상계2동", "상계3.4동", "상계5동", "상계6.7동", "상계8동", "상계9동", "상계10동"],
        "하계동": ["하계1동", "하계2동"],
        "공릉동": ["공릉1동", "공릉2동"]
    }
    
    # 지역명에 해당하는 키워드들 찾기
    search_terms = region_keywords.get(region_name, [region_name])
    
    # 검색 순서: 3단계 → 2단계 → 1단계
    for term in search_terms:
        # 3단계에서 먼저 검색 (가장 구체적)
        if '3단계' in df.columns:
            mask = df['3단계'].str.contains(term, na=False, case=False)
            matches = df[mask]
            if not matches.empty:
                return extract_coord_info(matches.iloc[0], region_name)
        
        # 2단계에서 검색
        if '2단계' in df.columns:
            mask = df['2단계'].str.contains(term, na=False, case=False)
            matches = df[mask]
            if not matches.empty:
                return extract_coord_info(matches.iloc[0], region_name)
        
        # 1단계에서 검색
        if '1단계' in df.columns:
            mask = df['1단계'].str.contains(term, na=False, case=False)
            matches = df[mask]
            if not matches.empty:
                return extract_coord_info(matches.iloc[0], region_name)
    
    return None

def extract_coord_info(row, region_name: str) -> Dict:
    """CSV 행에서 좌표 정보 추출"""
    try:
        # 경도(초/100), 위도(초/100) 값을 도 단위로 변환
        lon_decimal = convert_coord_to_decimal(row.get('경도(초/100)'))
        lat_decimal = convert_coord_to_decimal(row.get('위도(초/100)'))
        
        # 격자 좌표 (이미 변환된 값)
        grid_x = int(row.get('격자 X', 0))
        grid_y = int(row.get('격자 Y', 0))
        
        # 상세 주소 생성
        address_parts = []
        for col in ['1단계', '2단계', '3단계']:
            if col in row and pd.notna(row[col]) and row[col].strip():
                address_parts.append(row[col].strip())
        
        full_address = ' '.join(address_parts) if address_parts else region_name
        
        return {
            'name': region_name,
            'full_address': full_address,
            'latitude': lat_decimal,
            'longitude': lon_decimal,
            'grid_x': grid_x,
            'grid_y': grid_y,
            'found_in_csv': True
        }
    except Exception as e:
        print(f"좌표 정보 추출 오류: {e}")
        return None

def get_coordinates_for_weather(location: str) -> Optional[Dict]:
    """
    날씨 조회용 좌표 정보 반환
    CSV에서 찾지 못하면 기본값 사용
    """
    # CSV에서 검색
    coord_info = find_coordinates_by_region(location)
    if coord_info and coord_info['latitude'] and coord_info['longitude']:
        return coord_info
    
    # CSV에서 찾지 못한 경우 기본값 (기존 하드코딩 좌표들)
    fallback_coords = {
        "춘천": {"latitude": 37.8813, "longitude": 127.7298, "grid_x": 73, "grid_y": 134},
        "서울": {"latitude": 37.5665, "longitude": 126.9780, "grid_x": 60, "grid_y": 127},
        "노원": {"latitude": 37.6541, "longitude": 127.0568, "grid_x": 61, "grid_y": 129}
    }
    
    if location in fallback_coords:
        fallback = fallback_coords[location]
        return {
            'name': location,
            'full_address': location,
            'latitude': fallback['latitude'],
            'longitude': fallback['longitude'],
            'grid_x': fallback['grid_x'],
            'grid_y': fallback['grid_y'],
            'found_in_csv': False
        }
    
    # 완전히 찾지 못한 경우 춘천 기본값
    return {
        'name': location,
        'full_address': f"{location} (기본위치: 춘천)",
        'latitude': 37.8813,
        'longitude': 127.7298,
        'grid_x': 73,
        'grid_y': 134,
        'found_in_csv': False
    }

def get_base_time() -> str:
    """현재 시간 기준으로 적절한 base_time 반환 (단순화)"""
    now = get_korean_time()
    
    # 초단기실황은 매시 정각, 10분 이후 API 제공
    # 단순하게 현재 시간 사용
    return now.strftime('%H00')

def get_forecast_base_time() -> str:
    """초단기예보용 base_time 반환 (단순화된 버전)"""
    now = get_korean_time()
    
    # 매시 30분에 발표되고 40-45분에 API 제공
    # 단순하게 현재 시간 사용
    if now.minute >= 30:
        return now.strftime('%H30')
    else:
        return now.strftime('%H00')

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
        service_key: str = None,
        coords: Tuple[float, float] = None,
        location: str = "춘천"
) -> str:
    """
    현재 날씨 정보 조회
    • service_key : 기상청 API 키 (필수)
    • coords      : (lat, lon) 형식의 위·경도 튜플 (선택적)
    • location    : 지역명 (coords가 없을 때 사용)
    """
    if not service_key:
        return f"{location}의 날씨 정보를 가져올 수 없습니다. (API 키 없음)"

    # 좌표 정보 가져오기
    if coords:
        lat, lon = coords
        # 좌표로부터 가장 가까운 격자 찾기 (간단하게 기본 격자 사용)
        coord_info = get_coordinates_for_weather(location)
        grid_x, grid_y = coord_info['grid_x'], coord_info['grid_y']
        location_name = f"{location} (좌표: {lat:.4f}, {lon:.4f})"
    else:
        # 지역명으로 좌표 검색
        coord_info = get_coordinates_for_weather(location)
        grid_x, grid_y = coord_info['grid_x'], coord_info['grid_y']
        location_name = coord_info['full_address']
        print(f"📍 {location} → {location_name} (격자: {grid_x}, {grid_y}) [CSV 검색: {'✅' if coord_info['found_in_csv'] else '❌'}]")

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
        "nx": grid_x,
        "ny": grid_y,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data["response"]["header"]["resultCode"] != "00":
            return f"{location_name}의 날씨 정보를 가져오는데 실패했습니다."

        items = data["response"]["body"]["items"]["item"]

        # 필요한 값만 추림
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

def get_forecast_weather(
    service_key: str,
    hours: int = 3,
    location: str = "춘천"
) -> str:
    """
    초단기예보 정보를 가져옴 (최대 6시간)
    CSV에서 격자 좌표를 직접 사용
    """
    if not service_key:
        return f"{location}의 예보 정보를 가져올 수 없습니다. (API 키 없음)"

    # CSV에서 좌표 정보 가져오기
    coord_info = get_coordinates_for_weather(location)
    grid_x, grid_y = coord_info['grid_x'], coord_info['grid_y']
    location_name = coord_info['full_address']
    
    print(f"📍 {location} → {location_name} (격자: {grid_x}, {grid_y}) [CSV 검색: {'✅' if coord_info['found_in_csv'] else '❌'}]")

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
        "nx": grid_x,
        "ny": grid_y,
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

def get_short_term_forecast(
    service_key: str,
    hours: int = 12,
    location: str = "춘천"
) -> str:
    """
    단기예보 정보를 가져옴 (6시간 초과 ~ 5일 이내)
    """
    if not service_key:
        return f"{location}의 단기예보 정보를 가져올 수 없습니다. (API 키 없음)"

    # CSV에서 좌표 정보 가져오기
    coord_info = get_coordinates_for_weather(location)
    grid_x, grid_y = coord_info['grid_x'], coord_info['grid_y']
    location_name = coord_info['full_address']
    
    print(f"📍 {location} → {location_name} (격자: {grid_x}, {grid_y}) [단기예보 사용]")

    # 단기예보 발표시간 계산
    now = get_korean_time()
    base_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']
    
    # 현재 시간 기준으로 가장 최근 발표된 단기예보 시간 찾기
    current_hour = now.hour
    base_time = '2300'  # 기본값
    
    for i, bt in enumerate([2, 5, 8, 11, 14, 17, 20, 23]):
        if current_hour >= bt + 1:  # 발표 후 1시간 이후부터 사용 가능
            base_time = base_times[i]
        else:
            break

    base_date = now.strftime('%Y%m%d')
    
    # 단기예보 API 호출
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": service_key,
        "dataType": "JSON",
        "numOfRows": 200,  # 단기예보는 데이터가 많으므로 충분히 설정
        "pageNo": 1,
        "base_date": base_date,
        "base_time": base_time,
        "nx": grid_x,
        "ny": grid_y,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if data["response"]["header"]["resultCode"] != "00":
            return f"{location_name}의 단기예보 정보를 가져오는데 실패했습니다."

        items = data["response"]["body"]["items"]["item"]
        
        # 목표 시간 계산 (현재 시간 + hours)
        target_time = now + timedelta(hours=hours)
        target_date = target_time.strftime('%Y%m%d')
        target_hour = target_time.strftime('%H00')
        
        # 해당 시간의 예보 데이터 필터링
        target_items = [
            item for item in items 
            if item["fcstDate"] == target_date and item["fcstTime"] == target_hour
        ]
        
        if not target_items:
            return f"{location_name}의 {hours}시간 후 단기예보 데이터를 찾을 수 없습니다."
        
        # 결과 구성
        forecast_data = {item["category"]: item["fcstValue"] for item in target_items}
        
        result = [f"{location_name} {hours}시간 후 ({target_time.strftime('%m월 %d일 %H시')}) 예보:"]
        
        # 기온
        if "TMP" in forecast_data:
            result.append(f"🌡️ 기온: {forecast_data['TMP']}°C")
        
        # 하늘상태
        if "SKY" in forecast_data:
            sky_desc = parse_weather_category('SKY', forecast_data['SKY'])
            result.append(f"☁️ {sky_desc}")
        
        # 강수형태
        if (pty := forecast_data.get("PTY")) and pty != "0":
            result.append(f"🌧️ {parse_weather_category('PTY', pty)}")
        
        # 강수확률
        if "POP" in forecast_data:
            result.append(f"☔ 강수확률: {forecast_data['POP']}%")
        
        # 강수량
        if (pcp := forecast_data.get("PCP")) and pcp not in ("0", "-", ""):
            result.append(f"💧 {parse_weather_category('PCP', pcp)}")
        
        # 습도
        if "REH" in forecast_data:
            result.append(f"💨 습도: {forecast_data['REH']}%")
        
        # 풍속
        if "WSD" in forecast_data:
            result.append(f"🌬️ 풍속: {forecast_data['WSD']} m/s")

        return "\n".join(result)

    except requests.exceptions.RequestException as e:
        return f"{location_name}의 단기예보 정보를 가져오는데 실패했습니다. (네트워크 오류: {e})"
    except Exception as e:
        return f"{location_name}의 단기예보 정보를 파싱하는 데 실패했습니다. (데이터 오류: {e})"


def get_comprehensive_weather(service_key: str = None, location: str = "춘천") -> str:
    """현재 날씨 + 단기 예보 정보 통합"""
    current = get_current_weather(service_key, location=location)
    
    # 6시간 후와 24시간 후 예보 제공
    forecast_6h = get_forecast_weather(service_key, hours=6, location=location)
    forecast_24h = get_short_term_forecast(service_key, hours=24, location=location)
    
    return f"{current}\n\n=== 6시간 후 ===\n{forecast_6h}\n\n=== 24시간 후 ===\n{forecast_24h}"

# 테스트 함수
def test_coordinate_search():
    """좌표 검색 테스트"""
    test_locations = ["춘천", "서울", "노원", "효자동", "효자", "월계동", "중계동", "상계동"]
    
    print("=== 좌표 검색 테스트 ===")
    for location in test_locations:
        coord_info = find_coordinates_by_region(location)
        if coord_info:
            print(f"✅ {location}: {coord_info['full_address']} → "
                  f"위도: {coord_info['latitude']:.6f}, 경도: {coord_info['longitude']:.6f}, "
                  f"격자: ({coord_info['grid_x']}, {coord_info['grid_y']})")
        else:
            print(f"❌ {location}: 찾을 수 없음")

if __name__ == "__main__":
    test_coordinate_search()
