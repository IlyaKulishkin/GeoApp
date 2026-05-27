from celery import shared_task
from .models import Point
from .services.artifact_service import sync_artifacts_http
from .services.dadata_service import DadataService
from django.contrib.auth.models import User
from points.services.rabbitmq_service import publish_message, RabbitMQUnavailable
import logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def fetch_address_for_point(self, point_id):
    logger.info(f"Задача {self.name} запущена для point_id={point_id}")
    try:
        point = Point.objects.get(id=point_id)
        lat = float(point.location.y)
        lon = float(point.location.x)

        dadata_service = DadataService()
        address = dadata_service.get_address_by_coordinates(lat, lon)

        if address:
            point.address = address
            point.save(update_fields=['address'])
            logger.info(f"Адрес для точки {point_id} сохранён: {address}")
        else:
            logger.info(f"Адрес для точки {point_id} не найден")

    except Point.DoesNotExist:
        logger.info(f"Точка {point_id} не найдена")
    except Exception as exc:
        logger.info(f"Ошибка при получении адреса для точки {point_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def sync_artifacts_for_user(user_id, username, prefer_rabbitmq=True):
    if prefer_rabbitmq:
        try:
            publish_message("artifacts_request", {"user_id": user_id})
            logger.info(f"RabbitMQ command sent for user {username}")
            return {"status": "queued", "method": "rabbitmq", "user": username}
        except RabbitMQUnavailable as e:
            logger.warning(f"RabbitMQ unavailable, falling back to HTTP for user {username}: {e}")

    try:
        user = User.objects.only("id", "username").get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {"error": "User not found"}

    return sync_artifacts_http(user)


@shared_task
def sync_all_users():
    users = list(User.objects.filter(is_active=True).values("id", "username"))

    for user in users:
        sync_artifacts_for_user.delay(user["id"], user["username"], prefer_rabbitmq=True)

    logger.info(f"Started sync for {len(users)} users")
    return {"total_users": len(users)}
