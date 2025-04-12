import requests
from bs4 import BeautifulSoup
import config
import re

from openai import OpenAI

def get_naver_news_url(location = "서울", display = 10, start = 1) -> dict:
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
        "query": f"{location} 오늘 날씨 기상청",
        "display": display,
        "start": start,
        "sort": "date",
    }

    answer = requests.get(request_url, headers=headers, params=params)

    if answer.status_code == 200:
        return answer.json()
    else:
        raise Exception(f"NAVER 검색 API 호출 실패: {answer.status_code}, {answer.text}")


def fetch_article_content(link: str) -> str:
    """
    주어진 URL에서 날씨 뉴스 기사 콘텐츠를 가져옵니다.
    
    Args:
        link (str): 크롤링할 link.

    Returns:
        str: 날씨 뉴스 기사 콘텐츠.
    """
    response = requests.get(link)
    if response.status_code != 200:
        raise Exception(f"페이지 요청 실패: {response.status_code}")
    
    soup = BeautifulSoup(response.text, "html.parser")

    # 기사 본문 추출 (예: id="dic_area")
    content = soup.find(id="dic_area") or soup.find(class_="article-content") or soup.find("article")
    if not content:
        raise Exception("날씨 정보를 찾을 수 없습니다.")

    # 텍스트 정리 및 반환
    return content.get_text(strip=True)


def get_naver_news_crawler(location = "서울") -> list:
    """
    get_naver_news_url 함수를 통해 받아온 네이버 뉴스 url을 크롤링하는 함수.

    Args:
        location (str): 검색할 지역 (ex: "서울).

    Returns:
        list: 한 줄 요약된 뉴스들을 담은 리스트.
    """

    # TODO: flask로 요청 받은 값을 get_naver_news_url 함수에 인수 location으로 넘겨야 함.
    naver_news_data = get_naver_news_url(location)

    for items in naver_news_data["items"]:
        link = items["link"]
        print(link)

        try:
            article_content = fetch_article_content(link)

            # HTML 태그 형식 탐지해 지우기
            clean_article_content = re.sub(r'<.*?>', '', str(article_content))

            # 날씨 기사 요약하기
            summary_content = llm_summarize_news(clean_article_content)
        except Exception as e:
            print(e)
            continue

        print(summary_content)

def llm_summarize_news(article_content = "") -> str:
    """
    주어진 뉴스 기사 내용을 openAI API를 사용하여 한 줄로 요약합니다.

    Args:
        article_content (str): 날씨 기사 본문

    Returns:
        str: 한 줄 요약 문자열

    Raises:
        ValueError: 입력값이 비어 있거나 유효하지 않은 경우
    """

    # article_content 검증하기
    if (article_content == ""):
        raise ValueError("article_content가 인수로 입력되지 않았습니다!")

    # 1. OpenAI API 기본 세팅
    OPENAI_API_KEY = config.OPENAI_API_KEY
    client = OpenAI(api_key = OPENAI_API_KEY)

    # 3. system prompt, user prompt 세팅
    system_prompt = """당신은 전문 뉴스 요약 기자입니다.
    다음 규칙을 따르세요:
    1. 기사 내용을 한 줄로 요약하세요.
    2. 아침/낮 기온, 강수 확률, 체감온도 등 핵심 정보를 포함하세요.
    3. 숫자와 단위를 정확히 표기하세요."""

    user_prompt = f"""다음은 날씨 기사입니다:
    {article_content}
    이를 요약해주세요."""

    # 4. 요약 생성
    completion = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature = 0.3,
        max_tokens = 200,
    )

    return completion.choices[0].message.content.strip()


if __name__ == "__main__":
    get_naver_news_crawler()