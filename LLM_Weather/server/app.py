import json
from crawler.naver_news_crawler import export_news_summaries_json
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/weather/news")
async def get_weather_news_summaries(location: str):
    return json.loads(await export_news_summaries_json(location))