import json
import pika
from django.conf import settings


RABBITMQ_URL = getattr(
    settings,
    "RABBITMQ_URL",
    "amqp://guest:guest@rabbitmq:5672/"
)


class RabbitMQUnavailable(Exception):
    pass


def publish_message(queue_name: str, payload: dict):
    try:
        params = pika.URLParameters(RABBITMQ_URL)

        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(queue=queue_name, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        connection.close()

    except Exception as e:
        raise RabbitMQUnavailable(str(e))