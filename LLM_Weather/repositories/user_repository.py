from typing import Dict, List
from db.db_connection import get_db_cursor

class UserRepository:
    """사용자 작업을 위한 저장소"""
    
    @staticmethod
    def create(location: str) -> int:
        """새 사용자 생성"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (location) VALUES (?)",
                (location,)
            )
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(user_id: int) -> Dict[str, any]:
        """ID로 사용자 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, location, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            return dict(cursor.fetchone() or {})
    
    @staticmethod
    def get_all() -> Dict[str, List[Dict[str, any]]]:
        """모든 사용자를 location별로 그룹화하여 조회"""
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, location, created_at FROM users ORDER BY location, created_at")
            rows = cursor.fetchall()
            
            grouped_users = {}
            for row in rows:
                user_dict = dict(row)
                location = user_dict['location']
                if location not in grouped_users:
                    grouped_users[location] = []
                grouped_users[location].append(user_dict)
            
            return grouped_users

