import cv2
import pickle
import numpy as np
import datetime
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import time
import logging
from src.rabbitmq.client import RabbitMQClient
from src.ai.counter import IngotCounter
from src.db.database import DatabaseLogger
from src.config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def frame_consumer(processor_id, counting_line_x, queue_name, stop_event=None):
    rabbitmq_client = RabbitMQClient(
        settings.RABBITMQ_HOST, settings.RABBITMQ_PORT,
        settings.RABBITMQ_USER, settings.RABBITMQ_PASS
    )
    rabbitmq_client.connect()

    counter = IngotCounter(
        model_path='src/ai/model/best.pt',
        counting_line_x=counting_line_x,
        rabbitmq_client=rabbitmq_client,
        queue_name=queue_name,
        match_threshold=5
    )

    db_logger = DatabaseLogger()

    output_dir = f"output_frames/{processor_id}"
    os.makedirs(output_dir, exist_ok=True)

    frame_count = 0
    ingot_count = 0
    frame_width = 3840
    frame_height = 2160
    resize_factor = 0.5

    try:
        while stop_event is None or not stop_event.is_set():
            try:
                message = rabbitmq_client.basic_get(queue_name)
                if message is None:
                    logger.info(f"{processor_id} - No frames available, waiting...")
                    time.sleep(0.1)
                    continue

                compressed_frame = pickle.loads(message)
                frame = cv2.imdecode(np.frombuffer(compressed_frame, np.uint8), cv2.IMREAD_COLOR)
                if frame is None or frame.size != frame_width * frame_height * 3:
                    logger.warning(f"{processor_id} - Corrupted frame detected, skipping...")
                    continue
                
                frame = cv2.resize(frame, (int(frame.shape[1] * resize_factor), int(frame.shape[0] * resize_factor)))
                count, sizes, widths, results = counter.process_frame(frame)
                ingot_count += count

                for box in results[0].boxes:
                    x, y, w, h = box.xywh[0].tolist()
                    x1, y1 = int(x - w / 2), int(y - h / 2)
                    x2, y2 = int(x + w / 2), int(y + h / 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                cv2.line(frame, (counting_line_x, 0), (counting_line_x, frame.shape[0]), (0, 255, 0), 2)
                cv2.putText(frame, f"ingot_count: {ingot_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                frame_count += 1

                if count > 0:
                    frame_path = os.path.join(output_dir, f"frame_{frame_count:04d}.jpg")
                    cv2.imwrite(frame_path, frame)
                    logger.info(f"{processor_id} - Frame {frame_count} saved: ingot_count={ingot_count}")

                    _, encoded_frame = cv2.imencode('.jpg', frame)
                    frame_bytes = encoded_frame.tobytes()
                    # frame_datetime = datetime.datetime.now()
                    dt = datetime.fromtimestamp(timestamp, tz=ZoneInfo("Asia/Tehran"))
                    frame_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')
                    try:
                        db_logger.log_data(
                            camera_id=processor_id,
                            height=sizes[0] if sizes else 0,
                            width=widths[0] if widths else 0,
                            frame_datetime=frame_datetime,
                            frame_data=frame_bytes,
                            memo=f"Processed frame {frame_count}"
                        )
                    except Exception as db_error:
                        logger.error(f"{processor_id} - Database error: {db_error}")
                else:
                    logger.info(f"{processor_id} - Frame {frame_count} skipped: no ingots detected")

            except Exception as e:
                logger.error(f"{processor_id} - Error processing frame: {e}")
                time.sleep(0.1)
                continue

    except KeyboardInterrupt:
        logger.info(f"{processor_id} - Consumer interrupted, shutting down...")
    finally:
        try:
            db_logger.close()
            rabbitmq_client.close()
        except Exception as e:
            logger.error(f"{processor_id} - Error closing resources: {e}")