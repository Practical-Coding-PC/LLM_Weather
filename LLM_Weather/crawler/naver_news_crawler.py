import requests
import trafilatura
from bs4 import BeautifulSoup
import sys
import os
import json

# 현재 파일의 상위 디렉토리 경로를 가져오기
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re

from openai import OpenAI
from litellm import batch_completion
from dotenv import load_dotenv
# from flask import Flask, render_template, request

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return """
#         <h1>네이버 뉴스 요약</h1>
#         <form method="GET" action="/news">
#             <label for="location">지역:</label>
#             <input type="text" id="location" name="location" value="서울"><br><br>
#             <input type="submit" value="뉴스 요약 보기">
#         </form>
#     """

# @app.route('/news')
# def display_news():
#     location = request.args.get('location', '서울')
#     summary_contents = get_naver_news_crawler(location)
#     return render_template('news_list.html', summaries=summary_contents, location=location)


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

    url = f"https://search.naver.com/search.naver?where=news&query={location} 날씨"

    response = requests.get(url)

    # 상태 코드 추출 (200 정상)
    response.raise_for_status()
    print(f"Response Status Code: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    title_list = []
    link_list = []
 
    # 1. 뉴스 기사 블록(div) 리스트 추출
    news_item_divs = soup.select('div.group_news > ul > div > div > div > div')

    if news_item_divs:
        # 2. 각 뉴스 기사 블록에서 바로 아래 자식 div 리스트 추출
        news_content_divs = [
            child_div
            for news_div in news_item_divs
            for child_div in news_div.find_all('div', recursive=False)
        ]
        
        if news_content_divs:
            # 3. 각 기사 콘텐츠 div에서 두 번째 자식 div(기사 본문 정보 영역) 추출
            article_info_divs = [
                div.find_all('div', recursive=False)[1]
                for div in news_content_divs
                if len(div.find_all('div', recursive=False)) >= 2  # IndexError 방지
            ]
            
            if article_info_divs:
                for article_div in article_info_divs:
                    # 4. 기사 정보 div에서 <a> 태그의 href 속성(기사 링크) 추출
                    a_tag = article_div.find('a')
                    if a_tag and 'href' in a_tag.attrs:
                        link_list.append(a_tag['href'])

                    # 5. 기사 정보 div에서 <span> 태그의 제목 추출
                    span_tag = article_div.find('span')
                    if span_tag:
                        title = span_tag.get_text(strip=True)
                        print(f"span_tag = {title}")
                        title_list.append(title)
    
    print("\n--- 최종 추출된 링크 리스트 ---")
    print(link_list)

    # 각 URL에 대해 본문을 저장할 리스트 (루프 시작 전에 선언)
    news_list = []
    news_body = None

    for link in link_list:
        try:
            # 1. requests로 HTML 가져오기
            response = requests.get(link)
            response.raise_for_status() # 기본적인 HTTP 오류 확인
            
            # 2. trafilatura로 본문 추출 (response.text에서 추출)
            news_body = trafilatura.extract(response.text, include_comments=False)
            
            if not news_body: # 추출 실패 시 None/빈 문자열일 수 있음
                print(f" 링크: {link} -> 본문 추출 실패 (trafilatura 반환값 없음)")
        
        except Exception as e:
             print(f"  -> 오류 발생: {link} 처리 중 문제 발생 ({e})")

        # 3. 추출 결과 활용 (예: 리스트에 추가)
        if news_body:
            news_list.append(news_body)


    print(f"\n총 {len(news_list)}개의 뉴스 본문을 추출했습니다.")
    return link_list, title_list, news_list

def news_to_prompt(news_list: list, location: str) -> list:
    """
    주어진 뉴스 기사 내용들을 각각의 prompt으로 만든 후, 하나의 리스트로 반환합니다.

    Args:
        list: 날씨 기사 내용이 들어있는 리스트
        str: 검색할 지역 (ex: "서울).
    
    Returns:
        list: gemini API에 question으로 전달할 prompt들이 담긴 리스트
    """

    # 3. system prompt, user prompt 세팅
    system_prompt = {
        "role": "system",
        "content": f"""당신은 전문 뉴스 요약 기자입니다.
    다음 규칙을 따르세요:
    1. 기사 내용을 5줄 이내로, 지역 '{location}'을 중심으로 핵심만 간략히 요약하세요.
    2. 기사에 해당 지역({location})에 대한 내용이 없다면, 기사 전체를 간단히 요약하세요.
    3. 아침/낮 기온, 강수 확률, 체감온도 등 주요 정보를 포함하세요.
    4. 숫자와 단위는 정확하게 표기하세요.
    5. 만약 기사 내용이 날씨와 관련이 없다면 아무것도 출력하지 마세요.
    """
    }

    user_prompt = """다음은 날씨 기사입니다:
    {news}
    이를 요약해주세요."""

    prompts = [
        [
            system_prompt,
            {"role": "user", "content": user_prompt.format(news = news)}
        ]
        for news in news_list
    ]
    
    return prompts




def llm_summarize_news(prompts: list) -> str:
    """
    주어진 뉴스 기사 내용을 gemini API를 사용하여 한 줄로 요약합니다.

    Args:
        list: llm에 전달할 프롬프트들이 들은 리스트

    Returns:
        list: 기사 요약문이 들은 리스트

    Raises:
        ValueError: 입력값이 비어 있거나 유효하지 않은 경우
    """

    load_dotenv()

    if not prompts or not isinstance(prompts, list):
        raise ValueError("prompts가 인수로 입력되지 않았습니다!")

    # 4. 요약 생성
    responses = batch_completion(
        model = "gemini/gemini-2.0-flash",
        messages = prompts
    )

    return responses


async def export_news_summaries_json(location: str):
    link_list, title_list, news_list = get_naver_weather_news_crawler(location)
    prompts = news_to_prompt(news_list, location)

    response_list = [response["choices"][0]["message"]["content"] for response in llm_summarize_news(prompts)]

    export_list = [
        {
        "articleTitle": title,
        "articleSummary": summary,
        "articleUrl": link,
        }
        for title, summary, link in zip(title_list, response_list, link_list)
        if title and summary and link
    ]

    # with open("news_summaries.json", "w", encoding="utf-8") as f:
    #     json.dump(export_list, f, ensure_ascii=False, indent=2)
    
    # return json.dumps(export_list, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    export_news_summaries_json("춘천")