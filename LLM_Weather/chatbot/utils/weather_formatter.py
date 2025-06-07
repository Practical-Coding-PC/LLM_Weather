from typing import Dict, Any, List
from datetime import datetime, timedelta


def format_weather_data(weather_data: Dict[str, Any], location_name: str, forecast_type: str = "단기", target_hours: int = 0, full_day: bool = False) -> str:
    """
    기상청 API에서 받은 원시 데이터를 사용자 친화적인 형태로 변환합니다.
    
    Args:
        weather_data (Dict[str, Any]): 기상청 API 응답 데이터
        location_name (str): 지역명
        forecast_type (str): 예보 타입 ("초단기" 또는 "단기")
        target_hours (int): 몇 시간 후의 데이터를 원하는지 (0이면 가장 가까운 시간)
        full_day (bool): True이면 하루 전체 날씨 정보 반환
        
    Returns:
        str: 포맷된 날씨 정보
    """
    if weather_data.get("requestCode") != "200":
        return f"{location_name}의 날씨 정보를 가져오는데 실패했습니다."
    
    items = weather_data.get("items", [])
    if not items:
        return f"{location_name}의 날씨 데이터가 없습니다."
    
    # 시간별로 데이터 그룹화
    time_groups = {}
    for item in items:
        date_time = f"{item['fcstDate']}_{item['fcstTime']}"
        if date_time not in time_groups:
            time_groups[date_time] = {}
        time_groups[date_time][item['category']] = item['fcstValue']
    
    if not time_groups:
        return f"{location_name}의 날씨 데이터를 처리할 수 없습니다."
    
    if full_day:
        return _format_full_day_weather(time_groups, location_name, forecast_type)
    else:
        return _format_single_time_weather(time_groups, location_name, forecast_type, target_hours)


def _format_single_time_weather(time_groups: Dict[str, Dict[str, str]], location_name: str, forecast_type: str, target_hours: int) -> str:
    """특정 시간대의 날씨 정보를 포맷합니다."""
    sorted_times = sorted(time_groups.keys())
    
    if target_hours == 0:
        # 가장 가까운 시간대
        selected_time = sorted_times[0]
    else:
        # 현재 시간 + target_hours에 해당하는 시간대 찾기
        current_time = datetime.now()
        target_time = current_time + timedelta(hours=target_hours)
        target_date_str = target_time.strftime("%Y%m%d")
        target_hour_str = target_time.strftime("%H00")
        target_time_key = f"{target_date_str}_{target_hour_str}"
        
        # 정확한 시간이 있으면 사용, 없으면 가장 가까운 시간 사용
        if target_time_key in time_groups:
            selected_time = target_time_key
        else:
            # 가장 가까운 시간 찾기
            selected_time = sorted_times[0]
            for time_key in sorted_times:
                if time_key >= target_time_key:
                    selected_time = time_key
                    break
    
    forecast_data = time_groups[selected_time]
    
    # 시간 정보 파싱
    date_str = selected_time.split('_')[0]
    time_str = selected_time.split('_')[1]
    formatted_date = f"{date_str[4:6]}월 {date_str[6:8]}일"
    formatted_time = f"{time_str[:2]}시"
    
    result_parts = [f"{location_name} {forecast_type} 예보 ({formatted_date} {formatted_time}):"]
    result_parts.extend(_format_weather_details(forecast_data))
    
    return "\n".join(result_parts)


def _format_full_day_weather(time_groups: Dict[str, Dict[str, str]], location_name: str, forecast_type: str) -> str:
    """하루 전체 날씨 정보를 포맷합니다."""
    sorted_times = sorted(time_groups.keys())
    
    # 날짜별로 그룹화
    date_groups = {}
    for time_key in sorted_times:
        date_str = time_key.split('_')[0]
        if date_str not in date_groups:
            date_groups[date_str] = []
        date_groups[date_str].append(time_key)
    
    result_parts = [f"{location_name} {forecast_type} 예보 (하루 전체):"]
    
    for date_str in sorted(date_groups.keys()):
        formatted_date = f"{date_str[4:6]}월 {date_str[6:8]}일"
        result_parts.append(f"\n📅 {formatted_date}")
        
        # 하루 중 주요 시간대 (6시, 12시, 18시, 24시) 또는 사용 가능한 모든 시간대
        day_times = date_groups[date_str]
        
        # 주요 시간대 우선 선택 (있는 경우)
        key_times = []
        for hour in ["0600", "1200", "1800", "0000"]:
            target_time = f"{date_str}_{hour}"
            if target_time in day_times:
                key_times.append(target_time)
        
        # 주요 시간대가 없으면 사용 가능한 모든 시간대 사용
        if not key_times:
            key_times = day_times[:8]  # 최대 8개 시간대만 표시
        
        for time_key in key_times:
            time_str = time_key.split('_')[1]
            formatted_time = f"{time_str[:2]}시"
            forecast_data = time_groups[time_key]
            
            result_parts.append(f"  🕐 {formatted_time}")
            weather_details = _format_weather_details(forecast_data, indent="    ")
            result_parts.extend(weather_details)
    
    return "\n".join(result_parts)


def _format_weather_details(forecast_data: Dict[str, str], indent: str = "") -> List[str]:
    """날씨 상세 정보를 포맷합니다."""
    details = []
    
    # 기온 (TMP)
    if "TMP" in forecast_data:
        details.append(f"{indent}🌡️ 기온: {forecast_data['TMP']}°C")
    
    # 하늘상태 (SKY)
    if "SKY" in forecast_data:
        sky_value = forecast_data['SKY']
        if sky_value == "1":
            sky_desc = "☀️ 맑음"
        elif sky_value == "3":
            sky_desc = "⛅ 구름많음"
        elif sky_value == "4":
            sky_desc = "☁️ 흐림"
        else:
            sky_desc = f"🌫️ 하늘상태: {sky_value}"
        details.append(f"{indent}{sky_desc}")
    
    # 강수형태 (PTY)
    if "PTY" in forecast_data and forecast_data['PTY'] != "0":
        pty_value = forecast_data['PTY']
        if pty_value == "1":
            pty_desc = "🌧️ 비"
        elif pty_value == "2":
            pty_desc = "🌨️ 비/눈"
        elif pty_value == "3":
            pty_desc = "❄️ 눈"
        elif pty_value == "4":
            pty_desc = "🌦️ 소나기"
        else:
            pty_desc = f"🌧️ 강수형태: {pty_value}"
        details.append(f"{indent}{pty_desc}")
    
    # 강수확률 (POP)
    if "POP" in forecast_data:
        details.append(f"{indent}☔ 강수확률: {forecast_data['POP']}%")
    
    # 습도 (REH)
    if "REH" in forecast_data:
        details.append(f"{indent}💧 습도: {forecast_data['REH']}%")
    
    # 풍속 (WSD)
    if "WSD" in forecast_data:
        details.append(f"{indent}💨 풍속: {forecast_data['WSD']} m/s")
    
    return details 