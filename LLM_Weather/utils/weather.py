import requests
from bs4 import BeautifulSoup

def get_weather_from_naver(location="서울"):
    try:
        search_url = f"https://search.naver.com/search.naver?query={location}+날씨"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        weather_area = soup.find("div", class_="weather_info")
        temperature = weather_area.find("div", class_="temperature_text").text.strip()
        summary = weather_area.find("p", class_="summary").text.strip()
        rain = weather_area.find("dl", class_="summary_list").text.strip()

        return f"{location} 날씨 정보입니다.\n{temperature}, {summary}\n{rain}"
    except Exception as e:
        return f"{location}의 날씨 정보를 가져오는 데 실패했습니다. ({e})"