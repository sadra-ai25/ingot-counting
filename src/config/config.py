from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DB_SERVER: str
    DB_NAME: str
    USERNAME: str
    PASSWORD: str

    # # Cameras
    CAMERA1_RTSP_URL: str
    CAMERA1_COUNTING_LINE_X: int
    CAMERA2_RTSP_URL: str
    CAMERA2_COUNTING_LINE_X: int

    # Videos
    VIDEO1_COUNTING_LINE_X: int
    VIDEO1_PATH: str = str(Path(__file__).parent.parent.parent / "sample/video/1_2.mp4")

    # RabbitMQ
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASS: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()


