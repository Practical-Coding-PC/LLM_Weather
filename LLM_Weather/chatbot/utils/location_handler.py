import os
import sys
from typing import Optional, Dict, Any

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kakaoapi.get_city_from_coordinates import get_city_from_coordinates
from kakaoapi.get_coordinates_by_city import get_coordinates_by_city


class LocationHandler:
    """위치 관련 처리를 담당하는 클래스"""
    
    @staticmethod
    async def get_location_from_coords(latitude: float, longitude: float) -> str:
        """
        위도/경도로부터 지역명을 조회합니다.
        
        Args:
            latitude (float): 위도
            longitude (float): 경도
            
        Returns:
            str: 지역명
        """
        try:
            location = await get_city_from_coordinates(latitude, longitude)
            return location if location else "현재위치"
        except Exception as e:
            print(f"위치 조회 오류: {e}")
            return "현재위치"
    
    @staticmethod
    def is_current_location_request(location: str) -> bool:
        """
        현재 위치 요청인지 확인합니다.
        
        Args:
            location (str): 위치 문자열
            
        Returns:
            bool: 현재 위치 요청 여부
        """
        return (
            not location or  # 위치가 명시되지 않은 경우
            location.lower() in ['현재위치', '여기', '현재', 'current', 'here']
        )
    
    @staticmethod
    async def resolve_location(
        location: str, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None,
        forecast_service = None
    ) -> Dict[str, Any]:
        """
        위치 문자열을 실제 좌표로 변환합니다.
        
        Args:
            location (str): 위치 문자열
            latitude (float, optional): 현재 위치 위도
            longitude (float, optional): 현재 위치 경도
            forecast_service: ForecastService 인스턴스
            
        Returns:
            dict: 위치 정보 (name, lat, lon)
        """
        # 현재 위치 요청인지 확인
        if LocationHandler.is_current_location_request(location) and latitude and longitude:
            # 현재 위치 사용
            return {
                "lat": latitude,
                "lon": longitude
            }
        elif not location:
            # 위치가 명시되지 않았지만 현재 위치 정보도 없는 경우 기본값 사용
            location = "서울"
            if forecast_service:
                region_hit = await get_coordinates_by_city(location)
                if region_hit:
                    return {
                        "lat": region_hit["latitude"],
                        "lon": region_hit["longitude"]
                    }
            raise ValueError("위치 정보를 찾을 수 없습니다. 현재 위치를 허용하거나 구체적인 지역명을 입력해주세요.")
        else:
            # 지역명으로 좌표 검색
            region_hit = await get_coordinates_by_city(location)
            if region_hit:
                return {
                    "lat": region_hit["latitude"],
                    "lon": region_hit["longitude"]
                }