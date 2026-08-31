import json
import logging
import os

import pika

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")


class RabbitMQUnavailable(Exception):
    pass


def publish_message(queue_name: str, payload: dict):
    connection = None
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

        logger.info(f"Message published to queue '{queue_name}': user_id={payload.get('user_id')}")

    except Exception as e:
        logger.error(f"Failed to publish to '{queue_name}': {e}")
        raise RabbitMQUnavailable(str(e))
    finally:
        if connection and connection.is_open:
            connection.close()
