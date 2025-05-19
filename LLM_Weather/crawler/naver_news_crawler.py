import asyncio
import aiohttp
import requests
import trafilatura
from bs4 import BeautifulSoup
import os
import json


from litellm import completion
from litellm import batch_completion
from dotenv import load_dotenv

async def get_city_from_coordinates(latitude: float, longitude: float) -> str:
    """
    카카오맵 REST API를 사용하여 좌표로부터 행정구역(시) 이름을 가져옵니다.

    Args:
        latitude(float): 위도 값.
        longitude(float): 경도 값.

    Returns:
        str: 변환된 행정구역(시)의 이름입니다.
    """

    load_dotenv()

    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode"
    params = {
        "x": str(longitude),
        "y": str(latitude)
    }

    headers = {
        "Authorization": f"KakaoAK {os.environ.get('KAKAO_REST_API_KEY')}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:

            print(f"KakaoMap Response Status Code: {response.status}")
            
            json_response = await response.json()

            print(json_response.get('documents')[0])

            document = json_response.get('documents')[0]

            location = document.get('region_2depth_name')

            # 'region_2depth_name'(구 단위)이 비어있을 경우, 'region_1depth_name'(시도 단위)로 대체한다. ex) 세종특별자치시
            if location == '':
                location = document.get('region_1depth_name')
            

            # 시로 끝나는 경우 시를 제거한다.
            if location.endswith("시"):
                location = location.removesuffix("시")
            # 군으로 끝나는 경우 군을 제거한다.
            elif location.endswith("군"):
                location = location.removesuffix("군")
            # 구로 끝나는 경우 구를 제거한다.
            elif location.endswith("구"):
                location = location.removesuffix("구")
            
            return location



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

    if not prompts or not isinstance(prompts, list):
        raise ValueError("prompts가 인수로 입력되지 않았습니다!")

    # 4. 요약 생성
    responses = batch_completion(
        model = "gemini/gemini-2.0-flash",
        messages = prompts
    )

    return responses

def get_summarized_news(prompt, location):
    system_prompt = f"""당신은 제공된 '문맥' 속 뉴스가 '{location}' 지역의 날씨에 대한 내용을 명확하게 다루고 있는지 판단해야 합니다.
    다음 규칙을 엄격히 따르세요:
    1. '문맥'의 뉴스가 '{location}' 날씨에 대한 내용을 명확히 포함하고 있다면, 다른 추가 설명 없이 '답변: pass' 라고만 답변하세요.
    2. '문맥'의 뉴스가 '{location}' 날씨에 대한 내용을 포함하고 있지 않거나, 단순히 지역 이름만 언급되고 날씨와 관련이 없다면, 다른 추가 설명 없이 '답변: fail' 이라고만 답변하세요.

    문맥:
    {prompt}
    """.strip()

    # 요약 생성
    response = completion(
        model = "gemini/gemini-2.0-flash",
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"다음 문맥의 뉴스가 {location} 날씨에 대한 뉴스인지 판단하시오."}
        ]
    )

    return response.choices[0].message.content


async def export_news_summaries_json(latitude: float, longitude: float) -> dict:
    """
    좌표 기반 지역 날씨 뉴스를 Gemini로 요약 후, 관련 정보를 dict로 반환합니다.

    세부적으로는 좌표를 행정구역(시)으로 변환, 해당 지역의 날씨 뉴스 크롤링, Gemini API를 통한 기사 요약 과정이 포함됩니다.

    Args:
        latitude(float): 위도.
        longitude(float): 경도.

    Returns:
        dict: 뉴스의 'title', 'summary', 'url'을 포함하는 딕셔너리.
    """

    location = await get_city_from_coordinates(latitude, longitude)
    print(f"카카오맵에서 반환한 행정구역(시) 이름: {location}")

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

    # 파일 형태로 만들고 싶을 경우 사용
        # with open("news_summaries.json", "w", encoding="utf-8") as f:
    #     json.dump(export_list, f, ensure_ascii=False, indent=2)

    return json.dumps(export_list, ensure_ascii=False, indent=2)
    

if __name__ == "__main__":
    asyncio.run(export_news_summaries_json(33.25235, 126.5125556))