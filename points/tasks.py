from celery import shared_task
from .models import Point
from .services.dadata_service import DadataService
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