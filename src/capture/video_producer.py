import cv2
import pickle
from src.rabbitmq.client import RabbitMQClient
from src.config.config import settings

def video_producer(video_path, processor_id, stop_event=None):
    cap = cv2.VideoCapture(video_path)
    rabbitmq_client = RabbitMQClient(
        settings.RABBITMQ_HOST, settings.RABBITMQ_PORT,
        settings.RABBITMQ_USER, settings.RABBITMQ_PASS
    )
    rabbitmq_client.connect()

    frame_count = 0

    while cap.isOpened() and (stop_event is None or not stop_event.is_set()):
        ret, frame = cap.read()
        if not ret:
            break

        try:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            compressed_frame = buffer.tobytes()
            rabbitmq_client.publish(f"video_{processor_id}", pickle.dumps(compressed_frame))
            frame_count += 1
            # print(f"Video {processor_id} - Frame {frame_count} sent to RabbitMQ")

        except Exception as e:
            print(f"error in sending video {processor_id}: {e}")
            continue

    cap.release()
    rabbitmq_client.close()