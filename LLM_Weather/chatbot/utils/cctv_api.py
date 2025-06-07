import os
import requests
from typing import List, Dict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


class CCTVApiClient:
    """CCTV API 호출을 담당하는 클래스"""
    
    def __init__(self):
        """CCTVApiClient 초기화"""
        self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> str:
        """환경변수에서 CCTV API 키를 가져옵니다."""
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
        
        return api_key
    
    async def fetch_cctv_list(self, latitude: float, longitude: float) -> List[Dict]:
        """
        ITS API에서 CCTV 목록을 가져옵니다.
        
        Args:
            latitude (float): 중심 위도
            longitude (float): 중심 경도
            
        Returns:
            List[Dict]: CCTV 데이터 목록
        """
        if not self.api_key:
            return []

        # 조회할 type 목록
        types = ['its', 'ex']
        all_cctvs = []

        for cctv_type in types:
            try:
                cctvs = await self._fetch_cctv_by_type(cctv_type, latitude, longitude)
                all_cctvs.extend(cctvs)
            except Exception as e:
                print(f"CCTV API 호출 오류 (type={cctv_type}): {e}")
                continue
        
        print(f"총 {len(all_cctvs)}개의 CCTV 데이터를 가져왔습니다.")
        return all_cctvs
    
    async def _fetch_cctv_by_type(self, cctv_type: str, latitude: float, longitude: float) -> List[Dict]:
        """
        특정 타입의 CCTV 데이터를 가져옵니다.
        
        Args:
            cctv_type (str): CCTV 타입 ('its' 또는 'ex')
            latitude (float): 중심 위도
            longitude (float): 중심 경도
            
        Returns:
            List[Dict]: 해당 타입의 CCTV 데이터 목록
        """
        params = {
            'apiKey': self.api_key,
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
        
        if response.status_code != 200:
            print(f"CCTV API 요청 실패 (type={cctv_type}): {response.status_code}")
            return []
        
        data = response.json()
        if 'response' not in data or 'data' not in data['response']:
            return []
        
        cctvs = data['response']['data']
        cleaned_cctvs = []
        
        # 데이터 정제
        for cctv in cctvs:
            cleaned_cctv = self._clean_cctv_data(cctv)
            # 유효한 좌표가 있는 것만 추가
            if cleaned_cctv['coordx'] > 0 and cleaned_cctv['coordy'] > 0:
                cleaned_cctvs.append(cleaned_cctv)
        
        return cleaned_cctvs
    
    @staticmethod
    def _clean_cctv_data(cctv: Dict) -> Dict:
        """
        CCTV 데이터를 정제합니다.
        
        Args:
            cctv (Dict): 원본 CCTV 데이터
            
        Returns:
            Dict: 정제된 CCTV 데이터
        """
        return {
            'cctvname': cctv.get('cctvname', '').rstrip(';'),
            'cctvurl': cctv.get('cctvurl', '').rstrip(';'),
            'coordx': float(cctv.get('coordx', 0)) or 0,
            'coordy': float(cctv.get('coordy', 0)) or 0,
        } 