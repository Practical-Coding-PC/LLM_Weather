import requests
from bs4 import BeautifulSoup
import sys
import os

# 현재 파일의 상위 디렉토리 경로를 가져오기
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import re

from openai import OpenAI
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return """
        <h1>네이버 뉴스 요약</h1>
        <form method="GET" action="/news">
            <label for="location">지역:</label>
            <input type="text" id="location" name="location" value="서울"><br><br>
            <input type="submit" value="뉴스 요약 보기">
        </form>
    """

@app.route('/news')
def display_news():
    location = request.args.get('location', '서울')
    summary_contents = get_naver_news_crawler(location)
    return render_template('news_list.html', summaries=summary_contents, location=location)


def get_naver_news_url(location = "서울", display = 5, start = 1) -> dict:
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
    summary_contents = []

    for items in naver_news_data["items"]:
        link = items["link"]

        try:
            article_content = fetch_article_content(link)

            # HTML 태그 형식 탐지해 지우기
            clean_article_content = re.sub(r'<.*?>', '', str(article_content))

            # 날씨 기사 요약하기
            summary_content = llm_summarize_news(clean_article_content)
        except Exception as e:
            print(e)
            continue

        summary_contents.append(summary_content)
    
    return summary_contents



def get_naver_weather_news_crawler(location="서울") -> list:
    """
    네이버 뉴스 url을 크롤링하는 함수.
    네이버 API를 활용하여 크롤링하는 것은 중복된 뉴스 제목이 나오므로, 직접 requests를 활용해 개선하려 함.

    Args:
        location (str): 검색할 지역 (ex: "서울).

    Returns:
        list: 한 줄 요약된 뉴스들을 담은 리스트.
    """

    url = f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={location} 날씨"

    response = requests.get(url)
    response.raise_for_status()
    print(f"Response Status Code: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # 클래스명 'sds-comps-text-type-headline1'을 가진 span 요소를 선택한다.
    news_headline_elements = soup.select("span.sds-comps-text-type-headline1")

    # 클래스명 'sds-comps-text-type-body1'을 가진 span 요소를 선택한다.
    news_content_elements = soup.select("span.sds-comps-text-type-body1")

    # news_titles는 네이버 뉴스 title들을 담고 있는 리스트이다.
    news_titles = []
    if not news_headline_elements:
        print(f"'{location} 날씨'에 대해 'span.sds-comps-text-type-headline1' 선택자로 뉴스를 찾을 수 없습니다.")
        return []
        

    for element in news_headline_elements:
        # <span> 요소의 텍스트 내용을 직접 가져와, title들을 모두 리스트에 담는다.
        headline_text = element.get_text(strip=True)
        if headline_text:
            news_titles.append(headline_text)

    news_contents = []
    for element in news_content_elements:
        # <span> 요소의 텍스트 내용을 직접 가져와, content들을 모두 리스트에 담는다.
        content_text = element.get_text(strip=True)
        if content_text:
            news_contents.append(content_text)

    # 뉴스 제목, 내용 리스트 출력
    print(f"뉴스 제목: {news_titles}")
    print(f"뉴스 내용: {news_contents}")



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
    1. 기사 내용을 30자 내의 한 줄로 요약하세요.
    2. 아침/낮 기온, 강수 확률, 체감온도 등 핵심 정보를 포함하세요.
    3. 숫자와 단위를 정확히 표기하세요.
    4. 만약 기사 내용이 날씨와 관련없다면 출력하지 마시오."""

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


if __name__ == '__main__':
    # app.run(debug=True)
    print(get_naver_weather_news_crawler("서울"))