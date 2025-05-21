import asyncio
import time
import aiohttp
import trafilatura
from bs4 import BeautifulSoup
import os
import json
import litellm

from litellm import acompletion
from dotenv import load_dotenv
from typing import List, Tuple, Optional

async def get_city_from_coordinates(latitude: float, longitude: float) -> str:
    """
    카카오맵 REST API를 사용하여 좌표로부터 행정구역(시) 이름을 가져옵니다.

    Args:
        latitude (float): 위도 값.
        longitude (float): 경도 값.

    Returns:
        str: 변환된 행정구역(시)의 이름입니다. API 호출에 실패하거나 해당 좌표의
             행정구역 정보를 찾을 수 없는 경우, 빈 문자열("")이나 None을 반환할 수 있습니다.
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


async def fetch_and_extract_article(session: aiohttp.ClientSession, link: str) -> Optional[str]:
    """
    주어진 link의 뉴스 기사를 비동기적으로 크롤링하고, 본문을 추출하여 반환합니다.
    'trafilatura' 라이브러리의 extract 메소드를 사용하여 기사 본문을 추출합니다.

    Args:
        session (aiohttp.ClientSession): HTTP 요청을 위한 aiohttp 클라이언트 세션입니다.
        link (str): 크롤링 및 본문 추출을 수행할 기사의 URL입니다.

    Returns:
        Optional[str]: 추출된 기사 본문 문자열입니다.
                       추출에 실패하거나 오류가 발생하면 None을 반환합니다. 
    """
    try:
        async with session.get(link) as response:
            # HTTP 오류 발생 시, 예외를 발생시킨다.
            response.raise_for_status()
            article_html = await response.text()
        
        news_body = trafilatura.extract(article_html)

        if not news_body:
            print(f" 링크: {link} -> 본문 추출 실패 (trafilatura 반환값 없음)")

    except aiohttp.ClientError as e:
        print(f"  -> trafilatura 사용 중에 aiohttp 오류 발생: {link} 처리 중 문제 발생 ({e})")
        return None
    except Exception as e:
        print(f"  -> trafilatura 사용 중에 일반 오류 발생: {link} 처리 중 문제 발생 ({e})")
        return None
    
    return news_body


async def get_naver_weather_news_crawler(location="서울") -> Tuple[List[str], List[str], List[Optional[str]]]:
    """
    지정된 지역의 날씨 관련 네이버 뉴스 기사 URL을 비동기적으로 크롤링하고,
    각 URL로부터 HTML을 가져온 뒤 `trafilatura`를 사용하여 기사 본문을 추출합니다.

    이 함수는 다음 단계로 동작합니다:
    1. 네이버 뉴스 검색 페이지에 비동기적으로 접속하여 'location + 날씨' 키워드로 검색된 기사들의 링크를 수집합니다.
    2. 수집된 각 뉴스 기사 링크에 대해 비동기적으로 접속하여 HTML 내용을 가져옵니다.
    3. 각 기사의 HTML 내용에서 `trafilatura` 라이브러리를 사용해 원문 텍스트(본문)를 추출합니다.
    4. 성공적으로 추출된 모든 기사 본문 문자열을 리스트에 담아 반환합니다.

    Args:
        location (str): 날씨 뉴스를 검색할 지역 이름입니다. (예: "서울").
                        기본값은 "서울"입니다.

    Returns:
        Tuple[List[str], List[str], List[Optional[str]]]:
            다음 세 개의 리스트를 순서대로 담고 있는 튜플입니다:
            1. titles (List[str]): 추출된 뉴스 기사 제목들의 리스트.
            2. links (List[str]): 추출된 뉴스 기사 URL들의 리스트.
            3. news_list (List[Optional[str]]): 추출된 뉴스 기사 본문(텍스트)들의 리스트.
    """

    url = f"https://search.naver.com/search.naver?where=news&query={location} 날씨"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            print(f"네이버 뉴스 Response Status Code: {response.status}")
            response_text = await response.text()
        soup = BeautifulSoup(response_text, 'html.parser')

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

        tasks = [
            fetch_and_extract_article(session, link)
            for link in link_list
        ]

        news_list = await asyncio.gather(*tasks)


    print(f"\n총 {len(news_list)}개의 뉴스 본문을 추출했습니다.")
    return link_list, title_list, news_list


def news_to_prompt(title_list: list, news_list: list, location: str) -> list:
    """
    주어진 뉴스 기사 내용들을 각각의 prompt으로 만든 후, 하나의 리스트로 반환합니다.

    Args:
        title_list (list): 날씨 기사 제목이 들어있는 리스트
        news_list (list): 날씨 기사 내용이 들어있는 리스트
        location (str): 검색할 지역 (ex: "서울).
    
    Returns:
        list: gemini API에 question으로 전달할 prompt들이 담긴 리스트
    """

    # 3. system prompt, user prompt 세팅
    system_prompt = {
        "role": "system",
        "content": f"""당신은 전문 날씨 뉴스 요약 AI입니다. 당신의 임무는 매번 제공되는 단일 '기사 제목'과 '기사 내용'에만 엄격하게 근거하여 날씨 정보를 요약하는 것입니다. **'{location}' 지역의 날씨 정보를 우선적으로 다루되, 기사에 중요한 전국적인 날씨 정보나 전반적인 날씨 패턴에 대한 내용이 있다면 이 또한 요약에 포함할 수 있습니다.** 다른 기사의 정보나 당신의 외부 지식을 절대 사용해서는 안 됩니다. 요약 결과에 원본 기사의 제목이나 다른 기사의 제목을 포함하는 등, 날씨 요약과 직접 관련 없는 추가 정보는 절대 응답에 포함시키지 마십시오.

        다음 규칙을 반드시 엄격하게 준수해야 합니다:

        1.  주어진 글(기사 제목 및 내용 참고)이 **'{location}' 지역의 날씨와 직접적으로 관련되거나, 또는 중요한 전국적/일반적 날씨 정보를 포함하는 뉴스 기사**라고 판단될 경우에만 아래 2, 3, 4번 규칙에 따라 요약합니다. 
            만약 주어진 글이 날씨와 전혀 관련이 없거나, 뉴스 형식이 아니거나, ('{location}' 지역 날씨 정보와 중요한 전국적/일반적 날씨 정보를 포함하여) 유의미한 날씨 정보를 전혀 찾을 수 없는 경우, 당신의 응답은 **오직 "날씨 정보 없음"이어야 합니다. 이 외에 어떤 다른 단어, 문장, 기호, 설명, 또는 다른 기사의 제목도 절대 포함해서는 안 됩니다.**

        2.  '{location}' 지역 날씨 뉴스 기사를 요약할 때, **먼저 해당 지역의 구체적인 수치 정보(예: 아침/낮 기온, 강수 확률, 체감온도, 풍속, 습도 등)가 명시적으로 있다면, 이를 우선적으로 포함하여 핵심 내용을 간결하게 요약**해 주십시오. 숫자와 단위(예: ℃, mm, %)를 정확하게 표기해야 합니다. **그 다음으로, 기사에 중요한 전국적 날씨 정보나 전반적인 날씨 패턴에 대한 언급이 있다면, 이 내용도 간략하게 추가할 수 있습니다.** 전체 요약은 5줄 이내로 합니다.

        3.  규칙 2에서 언급된 '{location}' 지역의 상세한 수치 정보가 부족하거나 없더라도, 기사 내용 중 '{location}' 지역의 날씨에 관해 **조금이라도 언급된 내용, 정황, 또는 관련된 이야기**가 있다면 (예: 간략한 날씨 상태 변화, 날씨로 인한 간접적 영향, 주변 지역 날씨와 비교하며 언급된 내용, 과거 날씨에 대한 짧은 언급 등), **그 핵심적인 내용을 놓치지 말고 최대한 간결하게 요약에 먼저 포함**시키십시오. **그 다음으로, 기사에 중요한 전국적 날씨 정보나 전반적인 날씨 패턴에 대한 언급이 있다면, 이 내용도 간략하게 추가할 수 있습니다.** 전체 요약은 5줄 이내로 합니다.

        4.  '{location}' 지역에 관한 날씨 뉴스 기사이지만, 규칙 2의 구체적인 수치 정보도 없고 규칙 3에 따라 요약할 만한 '{location}' 지역 관련 날씨 언급이나 이야기도 **거의 찾을 수 없는 경우**, **기사에 중요한 전국적/일반적 날씨 정보가 있다면 해당 내용을 중심으로 요약하십시오.** 만약 이마저도 유의미하게 찾을 수 없다면, 당신의 응답은 **오직 "날씨 정보 없음"이어야 합니다. 이 외에 어떤 다른 단어, 문장, 기호, 설명, 또는 다른 기사의 제목도 절대 포함해서는 안 됩니다.**

        5.  요약은 항상 **날씨 정보 ('{location}' 지역 우선, 전국적 내용 포함 가능)** 에 초점을 맞추고, 날씨와 직접적인 관련이 없는 내용 (예: 일반 사건사고, 정치, 경제, 행사, 교통 정보 등)은 절대 포함시키지 마십시오. 
        """
    }

    user_prompt = """다음은 '{location}' 지역과 관련된 내용이 포함될 수 있는 기사입니다. 위에 제시된 시스템 프롬프트의 규칙에 따라 기사를 분석하고 요약해주세요.

    기사 제목:
    {title}

    기사 내용:
    {news}
    """


    prompts = [
        [
            system_prompt,
            {"role": "user", "content": user_prompt.format(location = location, title = title, news = news)}
        ]
        for title, news in zip(title_list, news_list)
    ]

    return prompts


async def llm_summarize_news(prompt: list) -> str:
    """
    주어진 단일 뉴스 기사 프롬프트(메시지 리스트)를 gemini API를 사용하여 
    5줄 이내로 비동기 요약하고, 요약 문자열을 반환합니다.

    Args:
        prompt (list): LLM에 전달할 단일 기사에 대한 메시지 리스트.
                                         (예: [{'role': 'system', ...}, {'role': 'user', ...}])

    Returns:
        str: 기사 요약문 문자열 또는 오류 발생 시 "날씨 정보 없음"
    """

    if not prompt or not isinstance(prompt, list):
        return "입력 프롬프트 오류"

    try:
        response = await litellm.acompletion(
            model="gemini/gemini-2.0-flash",
            messages=prompt
        )

        if response and response.choices and response.choices[0].message and response.choices[0].message.content:
            return response.choices[0].message.content
        else:
            return "날씨 정보 없음" # 문제 식별을 위한 명확한 반환값
        
    except Exception as e:
        return "날씨 정보 없음"


async def export_news_summaries_json(latitude: float, longitude: float) -> dict:
    """
    좌표 기반 지역 날씨 뉴스를 Gemini로 요약 후, 관련 정보를 dict로 반환합니다.

    세부적으로는 좌표를 행정구역(시)으로 변환, 해당 지역의 날씨 뉴스 크롤링, Gemini API를 통한 기사 요약 과정이 포함됩니다.

    Args:
        latitude (float): 위도.
        longitude (float): 경도.

    Returns:
        dict: 뉴스의 'title', 'summary', 'url'을 포함하는 딕셔너리.
    """

    start_time = time.time()
    location = await get_city_from_coordinates(latitude, longitude)
    print(f"카카오맵에서 반환한 행정구역(시) 이름: {location}")
    end_time = time.time()
    print(f"좌표 -> 행정구역(시) 변환 시간: {end_time - start_time}")

    start_time = time.time()
    link_list, title_list, news_list = await get_naver_weather_news_crawler(location)
    end_time = time.time()
    print(f"뉴스 크롤링 시간: {end_time - start_time}")

    start_time = time.time()
    prompts = news_to_prompt(title_list, news_list, location)
    end_time = time.time()
    print(f"프롬프트화에 걸리는 시간: {end_time - start_time}")

    start_time = time.time()
    tasks = [
        llm_summarize_news(prompt)
        for prompt in prompts
    ]

    response_list = await asyncio.gather(*tasks)
    end_time = time.time()
    print(f"LLM 뉴스 요약에 걸리는 시간: {end_time - start_time}")

    # 제외하고 싶은 LLM 답변 문자열
    undesired_summary_text = "날씨 정보 없음"

    export_list = [
        {
            "articleTitle": title,
            "articleSummary": summary,
            "articleUrl": link,
        }
        for title, summary, link in zip(title_list, response_list, link_list)
        if title and summary and link and (summary.strip() != undesired_summary_text)
    ]

    # 날씨 요약 기사는 최대 5개까지만 반환
    export_list = export_list[:5]

    return json.dumps(export_list, ensure_ascii=False, indent=2)
    

if __name__ == "__main__":
    asyncio.run(export_news_summaries_json(33.25235, 126.5125556))
    # asyncio.run(get_naver_weather_news_crawler())