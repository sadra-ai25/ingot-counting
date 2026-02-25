import pyodbc
import datetime
from src.config.config import settings

class DatabaseLogger:
    def __init__(self):
        self.conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={settings.DB_SERVER};'
            f'DATABASE={settings.DB_NAME};'
            f'UID={settings.USERNAME};'
            f'PWD={settings.PASSWORD}'
        )
        self.conn = pyodbc.connect(self.conn_str)
        self.cursor = self.conn.cursor()

    def log_data(self, camera_id, height, width, frame_datetime, frame_data, memo):
        try:
            self.cursor.execute(
                "EXEC aiStpInsertFrameIngot @cameraId=?, @width=?, @height=?, @frameDateTime=?, @frame=?, @memo=?",
                camera_id, width, height, frame_datetime, frame_data, memo
            )
            self.conn.commit()
            print(f"Logging to DB: camera_id={camera_id}, frame={frame_datetime}")
        except Exception as e:
            logger.warning("⚠️ Connection to SQL database failed, data will only be saved to local database.")
            logger.error(f"🚫 Error saving to database: {e}")

    def close(self):
        self.conn.close()