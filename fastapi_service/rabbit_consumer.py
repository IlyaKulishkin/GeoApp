import json
import os
import time
import pika
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from main import Artifact


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://geouser:geopass@db:5432/geopoints")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_rabbit_connection(max_retries=20, delay=3):
    for attempt in range(max_retries):
        try:
            return pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))

        except Exception as e:
            print(f"RabbitMQ unavailable: {e}")

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


def callback(ch, method, properties, body):
    data = json.loads(body)
    user_id = data["user_id"]
    db = SessionLocal()
    artifacts = db.query(Artifact).filter(
        Artifact.owner_id == user_id
    ).all()

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


def start_consumer():
    connection = get_rabbit_connection()
    channel = connection.channel()

    channel.queue_declare(
        queue='artifacts_request',
        durable=True
    )

    channel.basic_consume(
        queue='artifacts_request',
        on_message_callback=callback
    )
    print("FastAPI RabbitMQ consumer started")

    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
