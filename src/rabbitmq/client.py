import pika
import logging
import time

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self, host, port, user, password):
        self.credentials = pika.PlainCredentials(user, password)
        self.parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=self.credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}")
            time.sleep(0.01)
            raise

    def declare_queue(self, queue_name):
        if not self.connection or self.connection.is_closed:
            self.connect()
        self.channel.queue_declare(
            queue=queue_name,
            durable=True,  # صف پایدار باشد
            arguments={'x-max-length': 1000}  # محدودیت تعداد پیام
        )

    def publish(self, queue_name, message):
        self.declare_queue(queue_name)  # اطمینان از وجود صف
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # پیام پایدار
                expiration='60000'  # TTL 60 ثانیه
            )
        )
        # print(" [x] Sent frame to RabbitMQ")
        time.sleep(0.01)

    def basic_get(self, queue_name):
        try:
            self.declare_queue(queue_name)  # اطمینان از وجود صف
            method_frame, header_frame, body = self.channel.basic_get(queue_name)
            if method_frame:
                self.channel.basic_ack(method_frame.delivery_tag)
                return body
            return None
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            self.connect()
            return None

    def purge_queue(self, queue):
        self.channel.queue_purge(queue=queue)
        logger.info(f"Queue {queue} purged")

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()