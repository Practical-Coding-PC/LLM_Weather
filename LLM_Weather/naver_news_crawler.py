import requests
from bs4 import BeautifulSoup
import config
import re

def get_naver_news_url(location="서울", display=10, start=1) -> dict:
    """
    네이버 뉴스 검색 API를 이용해 네이버 뉴스 url를 가져오는 함수

    Args:
        location (str): 검색할 지역 (ex: "서울).
        display (int): 한 페이지에 표시할 뉴스 개수.
        start (int): 검색 시작 위치 (최대 1000).

    Returns:
        dict: API 응답 데이터(JSON 형식).
    """

    # 네이버 검색 API를 사용하기 위한 CLIENT_ID, CLIENT_SECRET
    NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
    NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET

    # 기본 네이버 뉴스 검색 URL과 쿼리 파라미터, 헤더 설정
    request_url = f"https://openapi.naver.com/v1/search/news.json?"
    

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": f"{location} 오늘 날씨",
        "display": display,
        "start": start
    }

    answer = requests.get(request_url, headers=headers, params=params)

    if answer.status_code == 200:
        return answer.json()
    else:
        raise Exception(f"NAVER 검색 API 호출 실패: {answer.status_code}, {answer.text}")


def get_naver_news_crawler(location = "서울") -> list:
    """
    get_naver_news_url 함수를 통해 받아온 네이버 뉴스 url을 크롤링하는 함수.

    Args:
        location (str): 검색할 지역 (ex: "서울).

    Returns:
        list: 한 줄 요약된 뉴스들을 담은 리스트.
    """

    try:
        # TODO: flask로 요청 받은 값을 get_naver_news_url 함수에 인수 location으로 넘겨야 함.
        naver_news_data = get_naver_news_url(location)

        for items in naver_news_data["items"]:
            # BeautifulSoup 기본 세팅
            headers = {"User-Agent": "Mozilla/5.0"}
            link = items["link"]
            request = requests.get(link, headers=headers)
            soup = BeautifulSoup(request.text, "html.parser")

            # 네이버 뉴스 기사 내용을 가져오기
            article_content = soup.find(id = "dic_area")

            # HTML 태그 형식 탐지해 지우기
            clean_article_content = re.sub(r'<.*?>', '', str(article_content))
            print(clean_article_content)
            print('----')

    except Exception as e:
        print(e)

def llm_summarize_news(article_content):
    """
    주어진 뉴스 기사 내용을 openAI API를 사용하여 한 줄로 요약합니다.

    Args:
        location (str): 검색할 지역 (ex: "서울).

    Returns:
        list: 한 줄 요약된 뉴스들을 담은 리스트.
    """
    pass


if __name__ == "__main__":
    get_naver_news_crawler()