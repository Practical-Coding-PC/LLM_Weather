import os
import re
import pytz
import warnings
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# 기상청 API 모듈 import
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.utils.ultra_short_term_forecast import fetch_ultra_short_term_forecast
from forecast.utils.short_term_forecast import fetch_short_term_forecast
from forecast.utils.weather import get_weather_from_naver
from forecast.utils.weather_kma import (
    get_current_weather, 
    get_forecast_weather, 
    get_specific_hour_forecast,
    get_short_term_forecast,
    get_comprehensive_weather
)

# urllib3 경고 무시 (macOS LibreSSL 호환성 문제)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")


class ForecastService:
    """
    날씨 예보 관련 비즈니스 로직을 처리하는 서비스 클래스
    """
    
    def __init__(self):
        # CSV 파일 경로 설정
        self.CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "forecast", "utils", "초단기예보-춘천-노원-csv.csv")
        self.region_df = pd.read_csv(self.CSV_PATH, encoding="utf-8")
        
        # 한국 시간대 설정
        self.KST = pytz.timezone('Asia/Seoul')
        
        # 지역 키워드 매핑
        self.REGION_KEYWORDS = {
            "서울": "서울특별시",
            "춘천": "춘천시",
            "노원": "노원구",
            "효자동": "효자1동",
            "효자": "효자1동",
            "월계동": "월계1동",
            "중계동": "중계본동",
            "상계동": "상계1동",
            "하계동": "하계1동"
        }
        
        # API 키 설정
        self.KMA_SERVICE_KEY = os.getenv('KMA_SERVICE_KEY')
        
    def get_korean_time(self) -> datetime:
        """
        한국 시간으로 현재 시간을 반환한다.
        
        Returns:
            datetime: 한국 시간대(Asia/Seoul)로 현재 시간을 나타내는 datetime 객체
        """
        return datetime.now(self.KST)
    
    def _convert(self, value: float) -> float:
        """
        CSV 컬럼 값이 도(°) 단위면 그대로 반환하고, 초/100 단위면 360000으로 나눠 도로 환산한다.
        
        Args:
            value (float): CSV 컬럼 값.
            
        Returns:
            float: 도(°) 단위로 변환된 값.
        """
        if value < 200:
            return float(value)
        return float(value) / 360000

    def get_ultra_short_term_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        초단기 예보 데이터를 반환한다.
        """
        return fetch_ultra_short_term_forecast(latitude, longitude)

    def get_short_term_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        단기 예보 데이터를 반환한다.
        """
        return fetch_short_term_forecast(latitude, longitude)
    
    def find_coords_by_keyword(self, msg: str) -> Optional[Dict[str, Any]]:
        """
        메시지에서 지역 키워드를 검색하여 해당 지역의 격자 좌표를 반환한다.
        
        Args:
            msg (str): 사용자 메시지.
            
        Returns:
            dict: 지역 이름, 격자 좌표(grid_x, grid_y), 위도(lat), 경도(lon)를 포함한 정보.
        """
        try:
            for key, alias in self.REGION_KEYWORDS.items():
                if key in msg:
                    mask = (
                        self.region_df["2단계"].str.contains(alias, na=False) |
                        self.region_df["3단계"].str.contains(alias, na=False)
                    )
                    matching_rows = self.region_df[mask]
                    
                    if not matching_rows.empty:
                        row = matching_rows.iloc[0]
                        # 격자 X, Y 좌표 사용 (기상청 API용)
                        grid_x = int(row["격자 X"])
                        grid_y = int(row["격자 Y"])
                        # 위도/경도도 백업으로 보관
                        lat = self._convert(row["위도(초/100)"])
                        lon = self._convert(row["경도(초/100)"])
                        return {
                            "name": key, 
                            "grid_x": grid_x, 
                            "grid_y": grid_y,
                            "lat": lat, 
                            "lon": lon
                        }
            return None
        except Exception as e:
            print(f"좌표 검색 오류: {e}")
            return None
    
    def analyze_weather_request(self, message: str, client_coords: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        사용자 메시지를 분석하여 지역 이름, 시간, 날씨 유형을 추출한다.
        
        Args:
            message (str): 사용자 메시지.
            client_coords (tuple[float, float] | None): 사용자의 현재 위치 좌표 (위도, 경도).
            
        Returns:
            dict: 지역 이름, 좌표, 날씨 유형, 미래 시간 정보.
        """
        
        # 지역 키워드 매칭
        region_hit = self.find_coords_by_keyword(message)
        if region_hit:
            location = region_hit["name"]
            coords = (region_hit["grid_x"], region_hit["grid_y"])  # 격자 좌표 사용
            lat_lon = (region_hit["lat"], region_hit["lon"])  # 위도/경도 보관
        else:
            location = "현재 위치"
            coords = client_coords
            lat_lon = client_coords

        # 시간 분석
        future_hours = None
        has_future = False
        
        now = self.get_korean_time()
        current_hour = now.hour
        current_minute = now.minute
        
        # 상대적 시간 표현 (띄어쓰기 허용, 다양한 표현 지원)
        time_patterns = [
            r'(\d+)\s*시간?\s*[후뒤]',  # "3시간 후", "3시간후"
            r'(\d+)\s*시간?\s*뒤',        # "3시간 뒤"
            r'(\d+)\s*시간?\s*뤮',        # "3시간 뤮"
        ]
        
        for pattern in time_patterns:
            m = re.search(pattern, message)
            if m:
                future_hours = int(m.group(1))
                has_future = True
                print(f"🔍 시간 패턴 매칭: '{message}' → {future_hours}시간 후")
                break
        
        # 절대적 시간 표현 (상대적 시간 패턴이 매칭되지 않은 경우에만)
        if not has_future and '오후' in message and '시' in message:
            pm_pattern = r'오후\s*(\d{1,2})시(?:반)?'
            pm_match = re.search(pm_pattern, message)
            if pm_match:
                target_hour = int(pm_match.group(1))
                if target_hour <= 12:
                    target_hour = target_hour + 12 if target_hour != 12 else 12
                target_minute = 30 if '반' in pm_match.group(0) else 0
                
                if target_hour > current_hour or (target_hour == current_hour and target_minute > current_minute):
                    future_hours = target_hour - current_hour
                else:
                    future_hours = 24 - current_hour + target_hour
                
                future_hours = int(future_hours)
                has_future = True
        
        elif not has_future and '오전' in message and '시' in message:
            am_pattern = r'오전\s*(\d{1,2})시(?:반)?'
            am_match = re.search(am_pattern, message)
            if am_match:
                target_hour = int(am_match.group(1))
                target_minute = 30 if '반' in am_match.group(0) else 0
                
                if target_hour > current_hour or (target_hour == current_hour and target_minute > current_minute):
                    future_hours = target_hour - current_hour
                else:
                    future_hours = 24 - current_hour + target_hour
                
                future_hours = int(future_hours)
                has_future = True
        
        # 자연어 시간 표현
        elif not has_future and '내일' in message:
            if '아침' in message:
                future_hours = 24 + 7 - current_hour
            elif '오전' in message:
                future_hours = 24 + 9 - current_hour
            elif '오후' in message:
                future_hours = 24 + 15 - current_hour
            elif '저녁' in message:
                future_hours = 24 + 18 - current_hour
            elif '밤' in message:
                future_hours = 24 + 22 - current_hour
            else:
                future_hours = 24
            has_future = True
        
        elif not has_future and '모레' in message:
            future_hours = 48
            has_future = True
        
        # weather_type 결정
        if has_future or any(w in message for w in ['예보', '나중', '앞으로', '미래']):
            weather_type = 'forecast'
        elif any(w in message for w in ['전체', '종합', '자세히', '상세']):
            weather_type = 'comprehensive'
        else:
            weather_type = 'current'

        print(f"🔎 날씨 요청 분석 결과:")
        print(f"  - 지역: {location}")
        print(f"  - 날씨 타입: {weather_type}")
        print(f"  - 미래 시간: {future_hours}")
        print(f"  - 미래 시간 여부: {has_future}")

        return {
            "location": location,
            "coords": coords,  # 격자 좌표 (X, Y)
            "lat_lon": lat_lon,  # 위도/경도 (예비용)
            "weather_type": weather_type,
            "future_hours": future_hours,
            "has_future_time": has_future
        }
    
    def get_weather_info(self, weather_request: Dict[str, Any]) -> str:
        """
        날씨 요청 정보를 기반으로 적절한 날씨 데이터를 반환한다.
        
        Args:
            weather_request (dict): 분석된 날씨 요청 정보. (지역 이름, 좌표, 날씨 유형, 미래 시간 정보)
            
        Returns:
            str: 날씨 정보 또는 오류 메시지.
        """
        location = weather_request['location']
        weather_type = weather_request['weather_type']
        future_hours = weather_request.get('future_hours', 6)
        coords = weather_request.get('coords')
        
        # 기상청 API 사용
        if self.KMA_SERVICE_KEY:
            try:
                if weather_type == "current":
                    # 현재 날씨 + 3시간 예보 조합
                    current_weather = get_current_weather(
                        service_key=self.KMA_SERVICE_KEY, 
                        coords=coords,
                        location=location
                    )
                    forecast_3h = get_forecast_weather(
                        service_key=self.KMA_SERVICE_KEY, 
                        hours=3,
                        location=location
                    )
                    return f"{current_weather}\n\n=== 향후 3시간 예보 ===\n{forecast_3h}"
                elif weather_type == 'forecast':
                    if future_hours <= 6:
                        # 특정 시간 후 날씨만 요청하는 경우
                        if future_hours and weather_request.get('has_future_time'):
                            return get_specific_hour_forecast(
                                service_key=self.KMA_SERVICE_KEY, 
                                hours=future_hours,
                                location=location
                            )
                        else:
                            return get_forecast_weather(
                                service_key=self.KMA_SERVICE_KEY, 
                                hours=future_hours,
                                location=location
                            )
                    elif future_hours <= 120:
                        # 6시간 초과 시 단기예보 사용
                        return get_short_term_forecast(
                            service_key=self.KMA_SERVICE_KEY,
                            hours=future_hours,
                            location=location
                        )
                    else:
                        try:
                            weather_info = get_weather_from_naver(location)
                            return f"{location}의 {future_hours}시간 후 날씨 정보:\n{weather_info}\n\n⚠️ 5일 초과 예보는 네이버 날씨를 통해 제공됩니다."
                        except Exception as e:
                            return f"{location}의 장기 예보 정보를 가져오는데 실패했습니다."
                elif weather_type == 'comprehensive':
                    return get_comprehensive_weather(
                        service_key=self.KMA_SERVICE_KEY,
                        location=location
                    )
            except Exception as e:
                print(f"기상청 API 오류: {e}")
        
        # Fallback: 네이버 크롤링 사용
        try:
            weather_info = get_weather_from_naver(location)
            return f"{location}의 날씨 정보:\n{weather_info}\n\n⚠️ 더 정확한 정보를 위해 기상청 API 키를 설정해주세요."
        except Exception as e:
            return f"{location}의 날씨 정보를 가져오는데 실패했습니다."
    
    def get_supported_locations(self) -> Dict[str, Any]:
        """
        지원되는 지역 목록을 반환한다.
        
        Returns:
            dict: 지원되는 지역 목록과 세부 정보를 포함한 딕셔너리
        """
        return {
            "locations": list(self.REGION_KEYWORDS.keys()),
            "details": {region: {"name": region} for region in self.REGION_KEYWORDS.keys()}
        }
    
    def is_kma_api_configured(self) -> bool:
        """
        기상청 API 키 설정 여부를 확인한다.
        
        Returns:
            bool: API 키가 설정되어 있으면 True, 아니면 False
        """
        return bool(self.KMA_SERVICE_KEY) 