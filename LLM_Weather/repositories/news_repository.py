from db.db_connection import get_db_cursor

class NewsRepository:
    """뉴스 작업을 위한 저장소"""
    
    @staticmethod
    def create(location, title, summary, link_url):
        """뉴스 항목 생성"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO news (location, title, summary, link_url) VALUES (?, ?, ?, ?)",
                (location, title, summary, link_url)
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_location(location):
        """위치로 뉴스 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, location, title, summary, link_url, created_at FROM news "
                "WHERE location = ? ORDER BY created_at DESC",
                (location,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_by_location_and_time_range(location, start_time, end_time, limit=10):
        """위치와 시간 범위로 뉴스 조회"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, location, title, summary, link_url, created_at FROM news "
                "WHERE location = ? AND created_at BETWEEN ? AND ? "
                "ORDER BY created_at DESC LIMIT ?",
                (location, start_time, end_time, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
