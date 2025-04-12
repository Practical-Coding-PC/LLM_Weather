import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# NAVER 검색 API 설정
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# OPENAI API KEY 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# TODO: GEMINI_API_KEY 환경 변수에서 가져온 후에 대해 코드 변경할 것
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# OpenAI API Key (환경변수에서 가져오거나 직접 입력)
GEMINI_API_KEY = "AIzaSyBh3ARBbmzbM6rxLm5FuFtZDjlFD2TtpTU"
# Gemini key
# AIzaSyAHH2HaJkE-1dNy6Sq6GhtneUMGAurbh2s
# AIzaSyC-BtbEw2RuUQvSxIY5UehKgTqIff3AN8A


# MySQL 설정
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"
MYSQL_HOST = "localhost"
MYSQL_DB = "interview_db"

# MySQL 연결 URL
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
