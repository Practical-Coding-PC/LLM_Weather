# LLM_Weather

## 서버 실행 방법
### 1. 세팅
- **환경 변수 세팅**: env_sample을 복사해 .env 파일에 복사한 후, 변수들의 값을 채워주세요.<br>
- **pip install**: fastapi, uvicorn, trafilatura, litellm 등 실행에 필요한 라이브러리를 import 해주세요.

### 2. 서버 실행/종료 방법
(1) 서버 실행: `uvicorn server.app:app --reload`<br>
(2) 서버 종료: `ctrl+c`

### 3. API 명세

#### 가. 날씨 기사 요약 정보 API 요청<br>

##### Request Syntax
```bash
curl --location 'http://127.0.0.1:8000/weather/news?latitude=37.33908333&longitude=127.9220556'
```

##### Request Elements
| Query Parameter | Type   |  Description                                 |
|-----------------|--------|-----------------------------------------|
| `latitude`      | float  | 위도 (예: `37.33908333`)                      |
| `longitude`     | float  | 경도 (예: `127.9220556`)                     |

##### Response Elements
| Element           | Type    | Description              |
|-------------------|---------|--------------------------|
| `articleTitle`    | string  | 기사 제목                |
| `articleSummary`  | string  | 기사 요약                |
| `articleUrl`      | string  | 기사 원문 URL            |

##### Response Example (200 OK)
```json
[
  {
    "title": "'세종시 국민체력100 체력증진교실' 시민 만족도 높아",
    "summary": "세종시체육회의 '2025년 국민체력100 체력증진교실'이 시민들의 적극적인 참여 속에 진행되고 있습니다.<br>만 19세 이상 세종시민을 대상으로 주 3회 진행되는 이 프로그램은 시민들의 건강 증진과 삶의 질 개선에 기여하고 있습니다.<br>참여자들은 체력 향상, 통증 완화, 수면 패턴 개선 등의 효과를 보고 있으며, 운동을 통해 자신감과 성취감을 얻고 있습니다.<br>세종시체육회는 시민들의 안전을 최우선으로 고려하여 프로그램을 운영하고 있으며, 생활체육 저변 확대에 힘쓰고 있습니다.<br>이 프로그램은 세종국민체력100 인증센터가 매년 최우수 평가를 받는데 기여하고 있습니다.",
    "link_url": "http://www.enewstoday.co.kr/news/articleView.html?idxno=2267561"
  },
  ...
]
```

<br><br>
#### 나. 초단기 예보 조회 API 요청

##### Request Syntax
```bash
curl --location 'http://127.0.0.1:8000/weather/ultra_short_term?latitude=37.879984&longitude=127.727479'
```

##### Request Elements
| Query Parameter | Type   |  Description                                 |
|-----------------|--------|-----------------------------------------|
| `latitude`      | float  | 위도 (예: `37.879984`)                      |
| `longitude`     | float  | 경도 (예: `127.727479`)                     |

##### Response Elements
| Element        | Type             | Description                         |
|----------------|------------------|-------------------------------------|
| `requestCode`  | string           | 처리 결과 코드 (“200” 등)           |
| `items`        | array of object  | 예보 항목 리스트                    |

##### items 객체 요소
| Element       | Type    | Description                                 |
|---------------|---------|---------------------------------------------|
| `fcstDate`    | string  | 예보 일자 (YYYYMMDD)                        |
| `fcstTime`    | string  | 예보 시각 (HHMM)                            |
| `category`    | string  | 예보 자료 구분 코드 (e.g. LGT, PTY, T1H 등) |
| `fcstValue`   | string  | 예보 값                                     |

##### Response Example (200 OK)

```json
{
  "requestCode": "200",
  "items": [
    {
      "fcstDate": "20250530",
      "fcstTime": "0700",
      "category": "LGT",
      "fcstValue": "0"
    },
    {
      "fcstDate": "20250530",
      "fcstTime": "0800",
      "category": "PTY",
      "fcstValue": "0"
    },
    ...
  ]
}
```

<br><br>
#### 다. 단기 예보 조회 API 요청

##### Request Syntax
```bash
curl --location 'http://127.0.0.1:8000/weather/short_term?latitude=37.879984&longitude=127.727479'
```

##### Request Elements
| Query Parameter | Type   |  Description                                 |
|-----------------|--------|-----------------------------------------|
| `latitude`      | float  | 위도 (예: `37.879984`)                      |
| `longitude`     | float  | 경도 (예: `127.727479`)                     |

##### Response Elements
| Element        | Type             | Description                         |
|----------------|------------------|-------------------------------------|
| `requestCode`  | string           | 처리 결과 코드 (“200” 등)           |
| `items`        | array of object  | 예보 항목 리스트                    |

##### items 객체 요소
| Element       | Type    | Description                                 |
|---------------|---------|---------------------------------------------|
| `fcstDate`    | string  | 예보 일자 (YYYYMMDD)                        |
| `fcstTime`    | string  | 예보 시각 (HHMM)                            |
| `category`    | string  | 예보 자료 구분 코드 (e.g. TMP, UUU, VVV 등) |
| `fcstValue`   | string  | 예보 값                                     |

##### Response Example (200 OK)
```json
{
  "requestCode": "200",
  "items": [
    {
      "fcstDate": "20250531",
       "fcstTime": "0000",
       "category": "TMP",
       "fcstValue": "14"
    },
    {
       "fcstDate": "20250531",
       "fcstTime": "0000",
       "category": "UUU",
       "fcstValue": "-0.4"
    },
    ...
  ]
}
```
<br><br>
#### 라. 서버 상태 확인

##### Request Syntax
```bash
curl --location 'http://127.0.0.1:8000/health'
```

##### Request Elements
해당 엔드포인트는 별도 요청 바디나 쿼리 파라미터가 없습니다.

##### Response Elements
##### Response Elements

| Element              | Type           | Description                                                                      |
| -------------------- | -------------- | -------------------------------------------------------------------------------- |
| status               | string         | 서버 상태를 나타냅니다. 가능한 값: `"healthy"` (정상)                   |
| gemini\_api          | string         | Gemini API 키 설정 여부를 나타냅니다. 가능한 값: `"configured"` (설정됨), `"not_configured"` (미설정) |
| kma\_api             | string         | 기상청 API 설정 여부를 나타냅니다. 가능한 값: `"configured"` (설정됨), `"not_configured"` (미설정)      |
| cctv\_api            | string         | CCTV API 키 설정 여부를 나타냅니다. 가능한 값: `"configured"` (설정됨), `"not_configured"` (미설정)   |
| supported\_locations | array\[string] | 서버가 현재 지원하는 지역 목록을 문자열 배열로 반환합니다. 예: `["서울", "춘천", "노원", ...]`                   |


##### Response Example (200 OK)
```json
{
    "status": "healthy",
    "gemini_api": "configured",
    "kma_api": "configured",
    "cctv_api": "configured",
    "supported_locations": [
        "서울",
        "춘천",
        "노원",
        "효자동",
        "효자",
        "월계동",
        "중계동",
        "상계동",
        "하계동"
    ]
}
```
<br><br>
#### 마. 참고 링크 (예보 자료 구분 코드 등)
<a href = "https://www.data.go.kr/data/15084084/openapi.do">기상청_단기예보 ((구)_동네예보) 조회서비스</a>
