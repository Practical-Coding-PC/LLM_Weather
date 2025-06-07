import os
import warnings
from typing import Dict, Any

# 기상청 API 모듈 import
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.utils.ultra_short_term_forecast import fetch_ultra_short_term_forecast
from forecast.utils.short_term_forecast import fetch_short_term_forecast

# urllib3 경고 무시 (macOS LibreSSL 호환성 문제)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")


class ForecastService:
    """
    날씨 예보 관련 비즈니스 로직을 처리하는 서비스 클래스
    """
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
