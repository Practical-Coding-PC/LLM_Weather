from db.db_connection import get_db_cursor
from typing import Dict, List, Optional

class NotificationRepository:
    """알림 작업을 위한 저장소"""
    
    @staticmethod
    def create(user_id: str, endpoint: str, expiration_time: Optional[int], p256dh_key: str, auth_key: str) -> int:
        """새 알림 구독 생성"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO notifications (user_id, endpoint, expiration_time, p256dh_key, auth_key) VALUES (?, ?, ?, ?, ?)",
                (user_id, endpoint, expiration_time, p256dh_key, auth_key)
            )
            return cursor.lastrowid
    
    @staticmethod
    def get_by_user_id(user_id: str) -> List[Dict[str, any]]:
        """사용자 ID로 알림 구독 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, endpoint, expiration_time, p256dh_key, auth_key, created_at FROM notifications WHERE user_id = ?",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_by_endpoint(endpoint: str) -> Optional[Dict[str, any]]:
        """엔드포인트로 알림 구독 조회 (중복 확인용)"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, endpoint, expiration_time, p256dh_key, auth_key, created_at FROM notifications WHERE endpoint = ?",
                (endpoint,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def update_subscription(user_id: str, endpoint: str, expiration_time: Optional[int], p256dh_key: str, auth_key: str) -> bool:
        """기존 알림 구독 업데이트"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "UPDATE notifications SET expiration_time = ?, p256dh_key = ?, auth_key = ? WHERE user_id = ? AND endpoint = ?",
                (expiration_time, p256dh_key, auth_key, user_id, endpoint)
            )
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_by_endpoint(endpoint: str) -> bool:
        """엔드포인트로 알림 구독 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM notifications WHERE endpoint = ?",
                (endpoint,)
            )
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_by_user_id(user_id: str) -> bool:
        """사용자 ID로 모든 알림 구독 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM notifications WHERE user_id = ?",
                (user_id,)
            )
            return cursor.rowcount > 0 