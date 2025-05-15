from contextlib import asynccontextmanager
import json
from crawler.naver_news_crawler import export_news_summaries_json
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# # AsysncIOScheduler instance 생성
# scheduler = AsyncIOScheduler(timezone = "Asia/Seoul")

# # 크롤링을 1분마다 하기 위한 lifespan context manager
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # yield 이전의 코드는 애플리케이션이 시작될 때 실행 (=startup)
#     print("FastAPI 서버가 시작되었습니다. 크롤링 스케줄러를 설정하고 시작합니다!")
#     scheduler.add_job(
#         export_news_summaries_json,
#         trigger = IntervalTrigger(seconds = 60),
#         args = ["춘천"], # 함수에 전달될 인자
#         id="news_crawl_job",  # 고유한 ID 부여
#         name="Naver News Crawler for Chuncheon",
#         replace_existing=True
#     )

#     scheduler.start()
#     print("스케줄러가 시작되었습니다!!")

#     yield

#     # yield 이후후의 코드는 애플리케이션이 종료될 때 실행 (=shutdown)
#     print("FastAPI 서버가 종료됩니다. 크롤링 스케줄러를 종료합니다!")
    


# app = FastAPI(lifespan = lifespan)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/weather/news")
async def get_weather_news_summaries(location: str):
    return json.loads(await export_news_summaries_json(location))