   
from ultralytics import YOLO
import cv2

class IngotCounter:
    def __init__(self, model_path, counting_line_x, rabbitmq_client, queue_name, match_threshold=5):
        self.model = YOLO(model_path)
        self.counting_line_x = counting_line_x
        self.match_threshold = match_threshold  # ترشولد برای انعطاف در تشخیص عبور
        self.counted_ids = set()  # مجموعه‌ای برای ذخیره IDهای شمرده‌شده
        self.rabbitmq_client = rabbitmq_client
        self.queue_name = queue_name

    def process_frame(self, frame):
        # پردازش فریم با مدل YOLO و فعال کردن ردیابی
        results = self.model.track(frame, persist=True)
        counted_ingots = []

        # بررسی هر باکس تشخیص داده‌شده
        for box in results[0].boxes:
            if box.id is None:
                continue
            id = int(box.id.item())
            x, y, w, h = box.xywh[0].tolist()
            centroid_x = x  # مختصات x مرکز باکس

            # شرط شمارش: وقتی مرکز شمش از خط سبز عبور کند و قبلاً شمرده نشده باشد
            if abs(centroid_x - self.counting_line_x) <= self.match_threshold and id not in self.counted_ids:
                counted_ingots.append((id, h, w))
                self.counted_ids.add(id)

        # محاسبه تعداد و اندازه‌ها
        count = len(counted_ingots)
        sizes = [size for _, size, _ in counted_ingots]
        widths = [width for _, _, width in counted_ingots]

        return count, sizes, widths, results