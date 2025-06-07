import os
import requests
import math
import sys
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kakaoapi.get_coordinates_by_city import get_coordinates_by_city

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

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

async def fetch_cctv_list(latitude: float, longitude: float) -> List[Dict]:
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
                'minX': longitude - 0.1,
                'maxX': longitude + 0.1,
                'minY': latitude - 0.1,
                'maxY': latitude + 0.1,
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
    # 1. 지역 좌표 찾기 (카카오 API 우선 사용)
    location_info = None
    location_name = location_text
    
    try:
        # 카카오 API로 좌표 조회
        coordinates = await get_coordinates_by_city(location_text)
        location_info = {
            'name': location_text,
            'lat': coordinates['latitude'],
            'lon': coordinates['longitude'],
            'full_name': location_text
        }
        print(f"카카오 API로 위치 조회 성공: {location_text}")
    except Exception as e:
        print(f"카카오 API 조회 실패: {e}")
    
    if not location_info:
        print(f"지역을 찾을 수 없습니다: {location_text}")
        return None
    
    target_lat = location_info['lat']
    target_lon = location_info['lon']
    location_name = location_info['name']
    
    print(f"검색 대상 지역: {location_name} ({target_lat:.6f}, {target_lon:.6f})")
    
    # 2. CCTV 목록 가져오기
    cctvs = await fetch_cctv_list(target_lat, target_lon)
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
