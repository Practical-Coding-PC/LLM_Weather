from contextlib import asynccontextmanager
import json
from crawler.naver_news_crawler import export_news_summaries_json
from forecast.ultra_short_term_forecast import fetch_ultra_short_term_forecast
from forecast.short_term_forecast import fetch_short_term_forecast
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from repositories.news_repository import NewsRepository
from contextlib import asynccontextmanager
from dotenv import load_dotenv

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv() # FastAPI를 구동할 때, 환경 변수를 로드한다.
    yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/weather/news")
async def get_weather_news_summaries(latitude: float, longitude: float):
    return json.loads(await export_news_summaries_json(latitude, longitude))

@app.get("/weather/news/test")
async def get_weather_news_summaries_test():
    return NewsRepository.get_by_location("춘천")

@app.get("/weather/ultra_short_term")
async def get_ultra_short_term_forecast(latitude: float, longitude: float):
    return await fetch_ultra_short_term_forecast(latitude, longitude)

@app.get("/weather/short_term")
async def get_short_term_forecast(latitude: float, longitude: float):
    return await fetch_short_term_forecast(latitude, longitude)