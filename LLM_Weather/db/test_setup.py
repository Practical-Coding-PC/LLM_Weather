#!/usr/bin/env python
import os
import sys
from datetime import datetime, timedelta, UTC

# 모듈을 가져올 수 있도록 부모 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.user_repository import UserRepository
from repositories.chat_repository import ChatRepository
from repositories.chat_message_repository import ChatMessageRepository
from repositories.news_repository import NewsRepository

def main():
    """데이터베이스 설정 및 리포지토리 테스트"""
    
    print("\n테스트 사용자 생성 중...")
    user_id = UserRepository.create("Test User")
    print(f"사용자 ID 생성됨: {user_id}")
    
    print("\n테스트 채팅 생성 중...")
    chat_id = ChatRepository.create(user_id)
    print(f"채팅 ID 생성됨: {chat_id}")
    
    print("\n테스트 메시지 추가 중...")
    msg1_id = ChatMessageRepository.create(chat_id, "user", "오늘 날씨는 어때?")
    print(f"메시지 ID 생성됨: {msg1_id}")
    
    msg2_id = ChatMessageRepository.create(chat_id, "assistant", "존나 더워요")
    print(f"메시지 ID 생성됨: {msg2_id}")
    
    print("\n테스트 뉴스 항목 생성 중...")
    news_id = NewsRepository.create(
        "춘천", 
        "비가 오네요", 
        "춘천에 비가 왔어요", 
        "https://example.com/news/123"
    )
    print(f"뉴스 ID 생성됨: {news_id}")
    
    print("\n채팅 기록 검색 중...")
    chat_history = ChatRepository.get_chat_with_messages(chat_id)
    print(f"채팅 데이터: {chat_history['chat']}")
    print("메시지:")
    for msg in chat_history["messages"]:
        print(f"  [{msg['role']}] {msg['content']}")
    
    print("\n서울 관련 뉴스 검색 중...")

    now = datetime.now(UTC)
    one_hour_ago = now - timedelta(hours=1)
    start_time = one_hour_ago.strftime("%Y-%m-%d %H:%M:%S")
    end_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"start_time: {start_time}, end_time: {end_time}")
    news_list = NewsRepository.get_by_location_and_time_range("춘천", start_time, end_time)
    for news in news_list:
        print(f"뉴스: {news['title']} - {news['summary']}")

if __name__ == "__main__":
    main() 