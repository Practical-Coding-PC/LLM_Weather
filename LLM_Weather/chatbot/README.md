# 챗봇 모듈 구조

## 📁 디렉토리 구조

```
chatbot/
├── chatbot_service.py          # 메인 챗봇 서비스 (핵심 로직)
├── utils/                      # 유틸리티 모듈들
│   ├── function_tools.py       # Function calling 도구 정의
│   ├── prompt_builder.py       # 프롬프트 생성
│   ├── function_executor.py    # Function call 실행
│   ├── location_handler.py     # 위치 처리
│   ├── cctv_utils.py          # CCTV 서비스 (리팩토링됨)
│   ├── cctv_api.py            # CCTV API 클라이언트
│   ├── geo_utils.py           # 지리적 계산 유틸리티
│   └── weather_formatter.py   # 날씨 데이터 포맷팅
└── README.md                   # 이 파일
```

## 🏗️ 주요 클래스 및 모듈

### 1. `ChatbotService` (메인 서비스)

- **역할**: 챗봇의 핵심 비즈니스 로직 처리
- **주요 기능**:
  - 사용자 메시지 처리
  - Gemini AI 모델과 통신
  - 대화 기록 관리
  - Function calling 결과 처리

### 2. `WeatherFunctionTools`

- **역할**: Gemini Function calling을 위한 도구 정의
- **주요 기능**:
  - 날씨 조회 함수 스키마 정의
  - 위치 조회 함수 스키마 정의
  - CCTV 조회 함수 스키마 정의

### 3. `PromptBuilder`

- **역할**: AI 모델에게 전달할 프롬프트 생성
- **주요 기능**:
  - Function calling용 프롬프트 생성
  - 최종 응답 생성용 프롬프트 생성
  - 대화 맥락을 고려한 프롬프트 구성

### 4. `FunctionExecutor`

- **역할**: Function calling으로 호출된 함수들 실행
- **주요 기능**:
  - 날씨 조회 함수 실행
  - 위치 좌표 조회 함수 실행
  - CCTV 정보 조회 함수 실행

### 5. `LocationHandler`

- **역할**: 위치 관련 처리
- **주요 기능**:
  - 좌표를 지역명으로 변환
  - 현재 위치 요청 감지
  - 위치 문자열을 좌표로 변환

### 6. `CCTVService` & `CCTVApiClient`

- **역할**: CCTV 관련 서비스 제공
- **주요 기능**:
  - ITS API를 통한 CCTV 데이터 조회
  - 가장 가까운 CCTV 찾기
  - API 클라이언트 관리

### 7. `GeoUtils`

- **역할**: 지리적 계산 유틸리티
- **주요 기능**:
  - 하버사인 공식을 이용한 거리 계산
  - 가장 가까운 지점 찾기
  - 좌표 유효성 검증

## 🚀 사용 방법

### 기본 사용법

```python
from chatbot.chatbot_service import ChatbotService

# 챗봇 서비스 초기화
chatbot = ChatbotService()

# 메시지 처리 (위치 정보 포함)
response = await chatbot.process_message(
    message="서울 날씨 어때?",
    user_id="user123",
    latitude=37.5665,  # 선택사항
    longitude=126.9780  # 선택사항
)

print(response["reply"])
```

### 개별 모듈 사용법

```python
# 1. 프롬프트 생성
from chatbot.utils.prompt_builder import PromptBuilder

prompt = PromptBuilder.build_function_call_prompt(
    user_message="춘천 날씨 알려줘",
    conversation_history="이전 대화..."
)

# 2. 위치 처리
from chatbot.utils.location_handler import LocationHandler

location_info = await LocationHandler.resolve_location(
    location="서울",
    latitude=37.5665,
    longitude=126.9780,
    forecast_service=forecast_service
)

# 3. CCTV 서비스
from chatbot.utils.cctv_utils import CCTVService

cctv_service = CCTVService()
nearest_cctv = await cctv_service.find_nearest_cctv_by_location("춘천")

# 4. 지리적 계산
from chatbot.utils.geo_utils import GeoUtils

distance = GeoUtils.calculate_distance(37.5665, 126.9780, 37.8813, 127.7298)
```
