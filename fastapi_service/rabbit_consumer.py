import json
import os
import time
import logging
import pika
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from main import Artifact

# Только добавляем логирование вместо print
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_rabbit_connection(max_retries=20, delay=3):
    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            logger.info(f"Connected to RabbitMQ on attempt {attempt + 1}")
            return connection
        except Exception as e:
            logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise


def publish_response(payload: dict):
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.queue_declare(queue='artifacts_response', durable=True)

    channel.basic_publish(
        exchange='',
        routing_key='artifacts_response',
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    connection.close()
    logger.info(f"Response published for user {payload.get('user_id')}")


def callback(ch, method, properties, body):
    data = json.loads(body)
    user_id = data["user_id"]
    logger.info(f"Processing request for user {user_id}")

    db = SessionLocal()
    artifacts = db.query(Artifact).filter(Artifact.owner_id == user_id).all()

    payload = {
        "user_id": user_id,
        "artifacts": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
            }
            for a in artifacts
        ]
    }

    publish_response(payload)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    db.close()
    logger.info(f"Processed {len(artifacts)} artifacts for user {user_id}")


def start_consumer():
    logger.info("Starting FastAPI RabbitMQ consumer...")
    connection = get_rabbit_connection()
    channel = connection.channel()

    channel.queue_declare(queue='artifacts_request', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='artifacts_request', on_message_callback=callback)

    logger.info("Consumer started, waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
