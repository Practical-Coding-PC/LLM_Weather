import requests
import config
def get_naver_news_crawler(location="서울", display=10, start=1) -> dict:
    """
    네이버 뉴스 검색 API를 이용해 뉴스 기사를 가져오는 함수

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


if __name__ == "__main__":
    try:
        naver_news_data = get_naver_news_crawler()

        for items in naver_news_data["items"]:
            print(items["description"])

    except Exception as e:
        print(e)