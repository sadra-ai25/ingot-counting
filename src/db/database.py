import pyodbc
import sqlite3
import datetime
import time
import threading
import logging
from src.config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseLogger:
    def __init__(self):
        self.sql_conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={settings.DB_SERVER};'
            f'DATABASE={settings.DB_NAME};'
            f'UID={settings.USERNAME};'
            f'PWD={settings.PASSWORD}'
        )
        self.sql_conn = None
        self.sql_cursor = None
        self.sqlite_conn = None
        self.sqlite_cursor = None
        self.connect_to_sql()
        self.connect_to_sqlite()
        threading.Thread(target=self.maintain_sql_connection, daemon=True).start()

    def connect_to_sql(self):
        try:
            self.sql_conn = pyodbc.connect(self.sql_conn_str)
            self.sql_cursor = self.sql_conn.cursor()
            logger.info("✅ Connected to SQL database.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to SQL database: {e}")
            self.sql_conn = None
            self.sql_cursor = None

    def connect_to_sqlite(self):
        try:
            self.sqlite_conn = sqlite3.connect('/app/database/local.db')    ## data warehouse 'local.db' sqlite3 ##
            self.sqlite_cursor = self.sqlite_conn.cursor()
            self.sqlite_cursor.execute('''
                CREATE TABLE IF NOT EXISTS frames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT,
                    height REAL,
                    width REAL,
                    frame_datetime TEXT,
                    frame_data BLOB,
                    memo TEXT
                )
            ''')
            self.sqlite_conn.commit()
            logger.info("✅ Connected to SQLite database.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to SQLite database: {e}")

    def maintain_sql_connection(self):
        while True:
            time.sleep(5)
            if self.sql_conn is None:
                logger.warning("⚠️ SQL connection is down, attempting to reconnect...")
                self.connect_to_sql()

    def log_data(self, camera_id, height, width, frame_datetime, frame_data, memo):
        try:
            self.sqlite_cursor.execute(
                "INSERT INTO frames (camera_id, height, width, frame_datetime, frame_data, memo) VALUES (?, ?, ?, ?, ?, ?)",
                (camera_id, height, width, frame_datetime.isoformat(), frame_data, memo)
            )
            self.sqlite_conn.commit()
            logger.info(f"💾 Logged to SQLite: camera_id={camera_id}, frame={frame_datetime}")
        except Exception as e:
            logger.error(f"❌ Error logging to SQLite: {e}")

        if self.sql_conn:
            try:
                self.sql_cursor.execute(
                    "EXEC aiStpInsertFrameIngot @cameraId=?, @width=?, @height=?, @frameDateTime=?, @frame=?, @memo=?",
                    camera_id, width, height, frame_datetime, frame_data, memo
                )
                self.sql_conn.commit()
                logger.info(f"💾 Logged to SQL: camera_id={camera_id}, frame={frame_datetime}")
            except Exception as e:
                logger.warning("⚠️ Connection to SQL database failed, data will only be saved to local database.")
                logger.error(f"❌ Error logging to SQL: {e}")
                self.sql_conn = None
                self.sql_cursor = None

    def close(self):
        if self.sql_conn:
            self.sql_conn.close()
            logger.info("🔌 SQL connection closed.")
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("🔌 SQLite connection closed.")