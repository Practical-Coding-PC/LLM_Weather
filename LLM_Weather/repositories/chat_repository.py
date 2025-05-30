from db.db_connection import get_db_cursor, get_db_connection
from datetime import datetime
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korean_time():
    """한국 시간으로 현재 시간 반환"""
    return datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')

class ChatRepository:
    """채팅 작업을 위한 저장소"""
    
    @staticmethod
    def create(user_id):
        """새로운 채팅 세션 생성"""
        korean_time = get_korean_time()
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO chats (user_id, created_at) VALUES (?, ?)",
                (user_id, korean_time)
            )
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(chat_id):
        """ID로 채팅 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, created_at FROM chats WHERE id = ?",
                (chat_id,)
            )
            return dict(cursor.fetchone() or {})
    
    @staticmethod
    def get_by_user_id(user_id, limit=10):
        """사용자 ID로 채팅 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, created_at FROM chats "
                "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_chat_with_messages(chat_id):
        """채팅과 모든 메시지 조회"""
        result = {"chat": None, "messages": []}
        
        with get_db_connection() as conn:
            # 채팅 정보 가져오기
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, user_id, created_at FROM chats WHERE id = ?",
                (chat_id,)
            )
            chat = cursor.fetchone()
            if not chat:
                return result
            
            result["chat"] = dict(chat)
            
            # 이 채팅의 메시지 가져오기
            cursor.execute(
                "SELECT id, chat_id, role, content, created_at FROM chat_messages "
                "WHERE chat_id = ? ORDER BY created_at",
                (chat_id,)
            )
            result["messages"] = [dict(row) for row in cursor.fetchall()]
            
        return result
    
    @staticmethod
    def delete(chat_id):
        """채팅과 메시지 삭제"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 외래 키 제약 조건으로 인해 메시지 먼저 삭제
            cursor.execute(
                "DELETE FROM chat_messages WHERE chat_id = ?",
                (chat_id,)
            )
            
            # 그 다음 채팅 삭제
            cursor.execute(
                "DELETE FROM chats WHERE id = ?",
                (chat_id,)
            )
            
            return cursor.rowcount > 0 