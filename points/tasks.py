from celery import shared_task
from dadata import Dadata
from django.conf import settings
from .models import Point
import logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def fetch_address_for_point(self, point_id):
    logger.info(f"Задача fetch_address_for_point запущена для point_id={point_id}")
    try:
        point = Point.objects.get(id=point_id)
        lat = float(point.location.y)
        lon = float(point.location.x)

        dadata = Dadata(settings.DADATA_TOKEN)
        result = dadata.geolocate(
            name="address",
            lat=lat,
            lon=lon,
            radius_meters=100
        )

        if result and result[0]:
            address = result[0]['unrestricted_value']
            point.address = address
            point.save(update_fields=['address'])
            print(f"Адрес для точки {point_id}: {address}")
        else:
            point.address = "Адрес не найден"
            point.save(update_fields=['address'])

    except Point.DoesNotExist:
        print(f"Точка {point_id} не найдена")
    except Exception as exc:
        print(f"Ошибка при получении адреса для точки {point_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)