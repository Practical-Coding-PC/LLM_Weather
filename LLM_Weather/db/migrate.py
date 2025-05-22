import sqlite3
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 데이터베이스 파일 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'weather.db')
MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')

def apply_migrations():
    """migrations 디렉토리의 모든 SQL 마이그레이션을 적용합니다"""
    # 데이터베이스 파일이 없으면 생성
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 데이터베이스에 연결
    logging.info(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # init.sql 마이그레이션 적용
    try:
        init_sql_path = os.path.join(MIGRATIONS_DIR, 'init.sql')
        logging.info(f"Applying migration from {init_sql_path}")
        
        with open(init_sql_path, 'r') as sql_file:
            sql_script = sql_file.read()
            cursor.executescript(sql_script)
            
        conn.commit()
        logging.info("Migration applied successfully")
    except Exception as e:
        conn.rollback()
        logging.error(f"Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    apply_migrations() 