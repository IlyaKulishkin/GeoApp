import json
import pika
import time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from points.models.api import Artifact


RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"


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


class Command(BaseCommand):
    help = "Consume artifacts from FastAPI"

    def handle(self, *args, **options):
        connection = get_rabbit_connection()
        channel = connection.channel()
        channel.queue_declare(queue='artifacts_response', durable=True)

        def callback(ch, method, properties, body):
            data = json.loads(body)

            user = User.objects.get(id=data["user_id"])

            for art in data["artifacts"]:
                Artifact.objects.update_or_create(
                    fastapi_id=art["id"],
                    defaults={
                        "name": art["name"],
                        "description": art.get("description"),
                        "owner": user,
                        "synced_at": timezone.now(),
                    }
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Synced {len(data['artifacts'])} artifacts"
                )
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(
            queue='artifacts_response',
            on_message_callback=callback
        )

        self.stdout.write("Waiting for messages...")

        channel.start_consuming()
