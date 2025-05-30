from db.db_connection import get_db_cursor
from datetime import datetime
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간으로 현재 시간 반환"""
    return datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')

class ChatMessageRepository:
    """채팅 메시지 작업을 위한 저장소"""
    
    @staticmethod
    def create(chat_id, role, content):
        """새로운 채팅 메시지 생성"""
        korean_time = get_korean_time()
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, role, content, korean_time)
            )
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(message_id):
        """ID로 메시지 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, chat_id, role, content, created_at FROM chat_messages "
                "WHERE id = ?",
                (message_id,)
            )
            return dict(cursor.fetchone() or {})
    
    @staticmethod
    def get_by_chat_id(chat_id):
        """채팅의 모든 메시지 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, chat_id, role, content, created_at FROM chat_messages "
                "WHERE chat_id = ? ORDER BY created_at",
                (chat_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_last_n_messages(chat_id, n=10):
        """채팅의 최근 N개 메시지 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, chat_id, role, content, created_at FROM chat_messages "
                "WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?",
                (chat_id, n)
            )
            messages = [dict(row) for row in cursor.fetchall()]
            return messages[::-1]  # Reverse to get chronological order
    
    @staticmethod
    def delete(message_id):
        """채팅 메시지 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM chat_messages WHERE id = ?",
                (message_id,)
            )
            return cursor.rowcount > 0 