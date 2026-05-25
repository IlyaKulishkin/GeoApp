import json
import pika
import time
import logging
import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from points.models.api import Artifact

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")


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


class Command(BaseCommand):
    help = "Consume artifacts from FastAPI"

    def handle(self, *args, **options):
        logger.info("Starting Artifact consumer...")

        connection = get_rabbit_connection()
        channel = connection.channel()
        channel.queue_declare(queue='artifacts_response', durable=True)

        def callback(ch, method, properties, body):
            try:
                data = json.loads(body)
                user_id = data["user_id"]
                artifacts_data = data.get("artifacts", [])

                user = User.objects.get(id=user_id)

                with transaction.atomic():
                    for art in artifacts_data:
                        Artifact.objects.update_or_create(
                            fastapi_id=art["id"],
                            defaults={
                                "name": art["name"],
                                "description": art.get("description"),
                                "owner": user,
                                "synced_at": timezone.now(),
                            }
                        )

                logger.info(f"Synced {len(artifacts_data)} artifacts for user {user.username}")
                self.stdout.write(
                    self.style.SUCCESS(f"Synced {len(artifacts_data)} artifacts")
                )

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except User.DoesNotExist:
                logger.error(f"User {user_id} not found")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        channel.basic_consume(queue='artifacts_response', on_message_callback=callback)

        self.stdout.write("Waiting for messages...")

        channel.start_consuming()
