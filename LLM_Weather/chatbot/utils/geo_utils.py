import math
from typing import Dict, List, Optional


class GeoUtils:
    """지리적 계산을 위한 유틸리티 클래스"""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        두 좌표 간의 거리를 계산합니다 (하버사인 공식 사용).
        
        Args:
            lat1 (float): 첫 번째 지점의 위도
            lon1 (float): 첫 번째 지점의 경도
            lat2 (float): 두 번째 지점의 위도
            lon2 (float): 두 번째 지점의 경도
            
        Returns:
            float: 두 지점 간의 거리 (km)
        """
        # 지구 반지름 (km)
        R = 6371
        
        # 위도와 경도를 라디안으로 변환
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        # 하버사인 공식
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    @staticmethod
    def find_nearest_point(
        target_lat: float, 
        target_lon: float, 
        points: List[Dict]
    ) -> Optional[Dict]:
        """
        주어진 좌표에서 가장 가까운 지점을 찾습니다.
        
        Args:
            target_lat (float): 기준점의 위도
            target_lon (float): 기준점의 경도
            points (List[Dict]): 검색할 지점들의 목록 (각 지점은 coordx, coordy 키를 가져야 함)
            
        Returns:
            Optional[Dict]: 가장 가까운 지점 (거리 정보 포함) 또는 None
        """
        if not points:
            return None
        
        nearest_point = None
        min_distance = float('inf')
        
        for point in points:
            try:
                point_lat = point['coordy']
                point_lon = point['coordx']
                
                # 거리 계산
                distance = GeoUtils.calculate_distance(target_lat, target_lon, point_lat, point_lon)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = point.copy()
                    nearest_point['distance'] = distance
                    
            except (KeyError, ValueError, TypeError) as e:
                print(f"지점 거리 계산 오류: {e}")
                continue
        
        return nearest_point
    
    @staticmethod
    def is_valid_coordinates(latitude: float, longitude: float) -> bool:
        """
        좌표가 유효한지 확인합니다.
        
        Args:
            latitude (float): 위도
            longitude (float): 경도
            
        Returns:
            bool: 좌표가 유효한지 여부
        """
        return (
            -90 <= latitude <= 90 and 
            -180 <= longitude <= 180 and
            latitude != 0 and longitude != 0
        ) 