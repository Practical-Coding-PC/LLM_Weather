import os
import sys
from typing import Dict, Optional

# 상위 디렉토리의 모듈들을 import하기 위해 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kakaoapi.get_coordinates_by_city import get_coordinates_by_city
from chatbot.utils.cctv_api import CCTVApiClient
from chatbot.utils.geo_utils import GeoUtils


class CCTVService:
    """CCTV 관련 서비스를 제공하는 클래스"""
    
    def __init__(self):
        """CCTVService 초기화"""
        self.api_client = CCTVApiClient()

    async def find_nearest_cctv_by_location(self, location_text: str) -> Optional[Dict]:
        """
        지역명을 기반으로 가장 가까운 CCTV를 찾습니다.
        
        Args:
            location_text (str): 검색할 지역명
            
        Returns:
            Optional[Dict]: 가장 가까운 CCTV 정보 또는 None
        """
        # 1. 지역 좌표 찾기
        location_info = await self._get_location_coordinates(location_text)
        if not location_info:
            print(f"지역을 찾을 수 없습니다: {location_text}")
            return None
        
        target_lat = location_info['lat']
        target_lon = location_info['lon']
        location_name = location_info['name']
        
        print(f"검색 대상 지역: {location_name} ({target_lat:.6f}, {target_lon:.6f})")
        
        # 2. CCTV 목록 가져오기
        cctvs = await self.api_client.fetch_cctv_list(target_lat, target_lon)
        if not cctvs:
            return None
        
        # 3. 가장 가까운 CCTV 찾기
        nearest_cctv = GeoUtils.find_nearest_point(target_lat, target_lon, cctvs)
        
        if nearest_cctv:
            nearest_cctv['target_location'] = location_name
            print(f"가장 가까운 CCTV: {nearest_cctv['cctvname']} (거리: {nearest_cctv['distance']:.2f}km)")
            print(f"MP4 URL: {nearest_cctv['cctvurl']}")
            return nearest_cctv
        
        return None
    
    async def _get_location_coordinates(self, location_text: str) -> Optional[Dict]:
        """
        지역명으로부터 좌표를 조회합니다.
        
        Args:
            location_text (str): 지역명
            
        Returns:
            Optional[Dict]: 위치 정보 (name, lat, lon) 또는 None
        """
        try:
            # 카카오 API로 좌표 조회
            coordinates = await get_coordinates_by_city(location_text)
            print(f"카카오 API로 위치 조회 성공: {location_text}")
            return {
                'name': location_text,
                'lat': coordinates['latitude'],
                'lon': coordinates['longitude']
            }
        except Exception as e:
            print(f"카카오 API 조회 실패: {e}")
            return None


# 하위 호환성을 위한 함수 (기존 코드에서 사용 중)
async def find_nearest_cctv(location_text: str) -> Optional[Dict]:
    """
    지역명을 기반으로 가장 가까운 CCTV 찾기 (하위 호환성용 함수)
    
    Args:
        location_text (str): 검색할 지역명
        
    Returns:
        Optional[Dict]: 가장 가까운 CCTV 정보 또는 None
    """
    service = CCTVService()
    return await service.find_nearest_cctv_by_location(location_text)
