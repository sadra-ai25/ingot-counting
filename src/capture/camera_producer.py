import subprocess
import pickle
import logging
import numpy as np
import cv2
from src.rabbitmq.client import RabbitMQClient
from src.config.config import settings
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def camera_producer(camera_url, camera_id, stop_event=None):
    logger.info(f"Starting camera producer for {camera_id} with URL: {camera_url}")
    ffmpeg_cmd = [
        'ffmpeg',
        '-rtsp_transport', 'tcp',
        "-skip_frame", "nokey",
        '-i', camera_url,
        '-r', "5",
        "-vsync", "0",
        '-f', 'image2pipe',
        '-pix_fmt', 'bgr24',
        '-vcodec', 'rawvideo',
        '-'
    ]

    frame_width = 3840
    frame_height = 2160
    frame_size = frame_width * frame_height * 3

    while stop_event is None or not stop_event.is_set():
        try:
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            rabbitmq_client = RabbitMQClient(
                settings.RABBITMQ_HOST, settings.RABBITMQ_PORT,
                settings.RABBITMQ_USER, settings.RABBITMQ_PASS
            )
            rabbitmq_client.connect()

            frame_count = 0
            buffer = bytearray()

            while process.poll() is None and not stop_event.is_set():
                data = process.stdout.read(4096)
                if not data:
                    logger.warning(f"Camera {camera_id} - No data from ffmpeg, retrying...")
                    break
                buffer.extend(data)

                while len(buffer) >= frame_size:
                    raw_frame = buffer[:frame_size]
                    buffer = buffer[frame_size:]
                    frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((frame_height, frame_width, 3))
                    _, buffer_img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    compressed_frame = buffer_img.tobytes()
                    rabbitmq_client.publish(f"camera_{camera_id}", pickle.dumps(compressed_frame))
                    frame_count += 1
                    logger.info(f"Camera {camera_id} - Frame {frame_count} sent to RabbitMQ")
                    time.sleep(0.5)

            process.terminate()
            rabbitmq_client.close()

        except Exception as e:
            logger.error(f"Error in camera producer for {camera_id}: {e}")
            time.sleep(5)

    logger.info(f"Stopping camera producer for {camera_id}")