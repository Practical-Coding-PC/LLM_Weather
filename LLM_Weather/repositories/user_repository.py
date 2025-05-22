from db.db_connection import get_db_cursor

class UserRepository:
    """사용자 작업을 위한 저장소"""
    
    @staticmethod
    def create(name):
        """새 사용자 생성"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (name) VALUES (?)",
                (name,)
            )
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(user_id):
        """ID로 사용자 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, name, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            return dict(cursor.fetchone() or {})
    
    @staticmethod
    def get_all():
        """모든 사용자 조회"""
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, name, created_at FROM users")
            return [dict(row) for row in cursor.fetchall()]
