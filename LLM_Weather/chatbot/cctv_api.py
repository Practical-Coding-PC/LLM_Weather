import os
import requests
import pandas as pd
import math
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import base64
from io import BytesIO

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# CSV 파일 경로
CSV_PATH = os.path.join(os.path.dirname(__file__), "초단기예보-춘천-노원-csv.csv")

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

def fetch_cctv_image_as_base64(url: str) -> Optional[str]:
    """
    CCTV 이미지를 직접 가져와서 base64로 변환 (CORS 문제 해결)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://its.go.kr/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 이미지 데이터를 base64로 인코딩
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        
        # Content-Type 추정
        content_type = response.headers.get('content-type', 'image/jpeg')
        
        return f"data:{content_type};base64,{image_base64}"
    
    except Exception as e:
        print(f"이미지 가져오기 실패: {e}")
        return None

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

def generate_cctv_html(cctv_data: Dict) -> str:
    """
    CCTV 정보를 HTML로 생성 (CORS 문제 해결)
    """
    if not cctv_data:
        return "<p>CCTV 정보를 찾을 수 없습니다.</p>"
    
    cctv_name = cctv_data.get('cctvname', 'CCTV')
    cctv_url = cctv_data.get('cctvurl', '')
    distance = cctv_data.get('distance', 0)
    location = cctv_data.get('target_location', '')
    image_base64 = cctv_data.get('image_base64', '')
    
    html = f"""
    <div style="border: 2px solid #4a90e2; border-radius: 10px; padding: 15px; margin: 10px 0; background: #f8f9fa;">
        <h3 style="color: #2c3e50; margin-bottom: 10px;">📹 {cctv_name}</h3>
        <p style="color: #666; margin-bottom: 10px;">📍 {location}에서 약 {distance:.1f}km 거리</p>
        
        <div style="text-align: center; margin: 15px 0;">
    """
    
    if image_base64:
        # base64 이미지 표시 (CORS 문제 해결됨)
        html += f"""
            <div style="position: relative; width: 100%; max-width: 400px; margin: 0 auto;">
                <img 
                    src="{image_base64}" 
                    alt="CCTV 실시간 이미지"
                    style="width: 100%; border-radius: 8px; cursor: pointer; display: block;"
                    onclick="refreshCctvImage('{cctv_url}', 'cctvImage_{hash(cctv_url) % 10000}')"
                    id="cctvImage_{hash(cctv_url) % 10000}"
                />
                <div style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                    LIVE
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #666; text-align: center;">
                💡 이미지를 클릭하면 새로고침됩니다
            </div>
        """
    else:
        # 이미지 로딩 실패시 대체 UI
        html += f"""
            <div style="width: 100%; max-width: 400px; height: 300px; background: #f0f0f0; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #999; border: 2px dashed #ddd; margin: 0 auto;">
                <div style="font-size: 48px; margin-bottom: 15px;">📹</div>
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">CCTV 이미지</div>
                <div style="font-size: 14px; text-align: center; margin-bottom: 15px;">실시간 도로 상황을 확인하세요</div>
                <button 
                    onclick="window.open('{cctv_url}', '_blank')"
                    style="background: #4a90e2; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;"
                >
                    🔗 새 탭에서 열기
                </button>
            </div>
        """
    
    html += f"""
        </div>
        
        <div style="text-align: center; margin-top: 10px;">
            <button 
                onclick="refreshCctvImage('{cctv_url}', 'cctvImage_{hash(cctv_url) % 10000}')" 
                style="background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; margin-right: 10px;"
            >
                🔄 새로고침
            </button>
            <button 
                onclick="window.open('{cctv_url}', '_blank')" 
                style="background: #4a90e2; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;"
            >
                🔗 원본 링크
            </button>
        </div>
        
        <p style="font-size: 12px; color: #999; margin-top: 10px; text-align: center;">
            💡 실시간 도로 상황 이미지입니다. 새로고침 버튼으로 최신 이미지를 확인하세요
        </p>
    </div>
    
    <script>
        // CCTV 이미지 새로고침 함수
        async function refreshCctvImage(url, imageId) {{
            const img = document.getElementById(imageId);
            if (!img) return;
            
            img.style.opacity = '0.5';
            
            try {{
                // 서버에서 이미지를 가져와서 업데이트
                const response = await fetch('/api/cctv-image', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ url: url }})
                }});
                
                if (response.ok) {{
                    const data = await response.json();
                    if (data.image_base64) {{
                        img.src = data.image_base64;
                    }}
                }}
            }} catch (error) {{
                console.error('이미지 업데이트 실패:', error);
                // 실패시 직접 URL 업데이트 시도
                img.src = url + '?t=' + new Date().getTime();
            }}
            
            img.style.opacity = '1';
        }}
        
        // 30초마다 자동 새로고침
        setInterval(function() {{
            refreshCctvImage('{cctv_url}', 'cctvImage_{hash(cctv_url) % 10000}');
        }}, 30000);
    </script>
    """
    
    return html

# 테스트 함수
async def test_cctv_search():
    """CCTV 검색 테스트"""
    test_locations = ["춘천", "효자동", "노원"]
    
    for location in test_locations:
        print(f"\n=== {location} CCTV 검색 ===")
        cctv = await find_nearest_cctv(location)
        if cctv:
            print(f"발견: {cctv['cctvname']} (거리: {cctv['distance']:.2f}km)")
            print(f"MP4 URL: {cctv['cctvurl']}")
            print(f"위치: {cctv['target_location']}")
        else:
            print("CCTV를 찾을 수 없습니다.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cctv_search())
