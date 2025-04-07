import os

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
