import os
import requests
import pandas as pd
import math
from typing import Dict, List, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# CSV 파일 경로
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "forecast", "utils", "초단기예보-춘천-노원-csv.csv")

# 지역 키워드 매핑
REGION_KEYWORDS = {
    "춘천": "춘천시",
    "효자동": "효자1동",
    "효자": "효자1동", 
    "노원": "노원구",
    "서울": "서울특별시",
    "월계동": "월계1동",
    "중계동": "중계본동",
    "상계동": "상계1동",
    "하계동": "하계1동"
}

def _convert_coord(value):
    """
    CSV 컬럼이 도(°) 단위면 그대로,
    초/100 단위면 360000으로 나눠 도로 환산한다.
    """
    if value < 200:  # 도 단위
        return float(value)
    # 초/100 단위면 도 단위로 변환
    return float(value) / 360000

def find_coords_by_keyword(location_text: str) -> Optional[Dict]:
    """
    지역 키워드로 좌표 찾기
    """
    try:
        region_df = pd.read_csv(CSV_PATH, encoding="utf-8")
    except Exception as e:
        print(f"CSV 파일 읽기 오류: {e}")
        return None
    
    for keyword, alias in REGION_KEYWORDS.items():
        if keyword in location_text:
            try:
                # 2단계(시/구) 또는 3단계(동) 컬럼에서 검색
                matching_rows = region_df[
                    (region_df["2단계"].str.contains(alias, na=False)) |
                    (region_df["3단계"].str.contains(alias, na=False))
                ]
                
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    lat = _convert_coord(row["위도(초/100)"])
                    lon = _convert_coord(row["경도(초/100)"])
                    
                    return {
                        "name": keyword,
                        "lat": lat,
                        "lon": lon,
                        "full_name": f"{row['1단계']} {row['2단계']} {row.get('3단계', '')}"
                    }
            except Exception as e:
                print(f"좌표 변환 오류 ({keyword}): {e}")
                continue
    
    return None

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    두 좌표 간의 거리를 계산 (km)
    """
    # 하버사인 공식
    R = 6371  # 지구 반지름 (km)
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

async def fetch_cctv_list() -> List[Dict]:
    """
    ITS API에서 CCTV 목록을 가져오기
    """
    api_key = os.getenv('REACT_APP_CCTV_API_KEY')
    if not api_key:
        # 기존 .env 파일에서 CCTV API 키 확인
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'), 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_CCTV_API_KEY='):
                        api_key = line.split('=')[1].strip()
                        break
        except Exception as e:
            print(f"환경 변수 파일 읽기 오류: {e}")
    
    if not api_key:
        print("⚠️ REACT_APP_CCTV_API_KEY가 설정되지 않았습니다!")
        return []

    # 조회할 type 목록
    types = ['its', 'ex']
    all_cctvs = []

    for cctv_type in types:
        try:
            params = {
                'apiKey': api_key,
                'type': cctv_type,
                'cctvType': '2',      # 동영상(mp4)
                'minX': 124.61167,
                'maxX': 131.87222,
                'minY': 33.11028,
                'maxY': 38.61111,
                'getType': 'json',
            }
            
            url = 'https://openapi.its.go.kr:9443/cctvInfo'
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'data' in data['response']:
                    cctvs = data['response']['data']
                    
                    # 데이터 정제
                    for cctv in cctvs:
                        cleaned_cctv = {
                            'cctvname': cctv.get('cctvname', '').rstrip(';'),
                            'cctvurl': cctv.get('cctvurl', '').rstrip(';'),
                            'coordx': float(cctv.get('coordx', 0)) or 0,
                            'coordy': float(cctv.get('coordy', 0)) or 0,
                        }
                        # 유효한 좌표가 있는 것만 추가
                        if cleaned_cctv['coordx'] > 0 and cleaned_cctv['coordy'] > 0:
                            all_cctvs.append(cleaned_cctv)
            else:
                print(f"CCTV API 요청 실패 (type={cctv_type}): {response.status_code}")
                
        except Exception as e:
            print(f"CCTV API 호출 오류 (type={cctv_type}): {e}")
            continue
    
    print(f"총 {len(all_cctvs)}개의 CCTV 데이터를 가져왔습니다.")
    return all_cctvs

async def find_nearest_cctv(location_text: str) -> Optional[Dict]:
    """
    지역명을 기반으로 가장 가까운 CCTV 찾기
    """
    # 1. 지역 좌표 찾기
    location_info = find_coords_by_keyword(location_text)
    if not location_info:
        print(f"지역을 찾을 수 없습니다: {location_text}")
        return None
    
    target_lat = location_info['lat']
    target_lon = location_info['lon']
    location_name = location_info['name']
    
    print(f"검색 대상 지역: {location_name} ({target_lat:.6f}, {target_lon:.6f})")
    
    # 2. CCTV 목록 가져오기
    cctvs = await fetch_cctv_list()
    if not cctvs:
        return None
    
    # 3. 가장 가까운 CCTV 찾기
    nearest_cctv = None
    min_distance = float('inf')
    
    for cctv in cctvs:
        try:
            cctv_lat = cctv['coordy']
            cctv_lon = cctv['coordx']
            
            # 거리 계산
            distance = calculate_distance(target_lat, target_lon, cctv_lat, cctv_lon)
            
            if distance < min_distance:
                min_distance = distance
                nearest_cctv = cctv.copy()
                nearest_cctv['distance'] = distance
                nearest_cctv['target_location'] = location_name
        except Exception as e:
            print(f"CCTV 거리 계산 오류: {e}")
            continue
    
    if nearest_cctv:
        print(f"가장 가까운 CCTV: {nearest_cctv['cctvname']} (거리: {min_distance:.2f}km)")
        print(f"MP4 URL: {nearest_cctv['cctvurl']}")
        return nearest_cctv
    
    return None
