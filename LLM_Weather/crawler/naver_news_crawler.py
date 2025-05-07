import requests
import trafilatura
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
    가져온 url을 통해 trafilatura로 뉴스 본문을 추출한다.

    Args:
        location (str): 검색할 지역 (ex: "서울).

    Returns:
        list: 한 줄 요약된 뉴스들을 담은 리스트.
    """

    url = f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={location} 날씨"

    response = requests.get(url)

    # 상태 코드 추출 (200 정상)
    response.raise_for_status()
    print(f"Response Status Code: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # CSS 선택자로 클래스가 lu8Lfh20c9DvvP05mqBf.OmR0jkNgHXA6BZNhMfn2인 <a> 태그 리스트를 가져오기
    a_tag_list = soup.select("a.lu8Lfh20c9DvvP05mqBf.OmR0jkNgHXA6BZNhMfn2")
    
    # 각 <a> 태그에서 href 속성 값 추출하기
    extracted_hrefs = []

    if a_tag_list:
        for a_tag in a_tag_list:
            href_value = a_tag.get('href')
            
            if href_value:
                extracted_hrefs.append(href_value)
    else:
         print("클래스 'lu8Lfh20c9DvvP05mqBf.OmR0jkNgHXA6BZNhMfn2'를 가진 <a> 태그를 찾지 못했습니다.")
    

    print("\n--- 최종 추출된 href 리스트 ---")
    print(extracted_hrefs)

    # 각 URL에 대해 본문을 저장할 리스트 (루프 시작 전에 선언)
    all_news_bodies = []
    news_body = None

    for link in extracted_hrefs:
        try:
            # 1. requests로 HTML 가져오기
            response = requests.get(link)
            response.raise_for_status() # 기본적인 HTTP 오류 확인
            
            # 2. trafilatura로 본문 추출 (response.text에서 추출)
            news_body = trafilatura.extract(response.text, include_comments=False)
            
            if not news_body: # 추출 실패 시 None/빈 문자열일 수 있음
                print(f"  -> 본문 추출 실패 (trafilatura 반환값 없음)")
        
        except Exception as e:
             print(f"  -> 오류 발생: {link} 처리 중 문제 발생 ({e})")

        # 3. 추출 결과 활용 (예: 리스트에 추가)
        if news_body:
            print(f"  -> 본문 추출 성공 \n {news_body}-") # 확인용 출력
            print("----------------")
            all_news_bodies.append(news_body)


    print(f"\n총 {len(all_news_bodies)}개의 뉴스 본문을 추출했습니다.")



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
    get_naver_weather_news_crawler("춘천")