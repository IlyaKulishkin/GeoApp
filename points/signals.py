from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models.api import Point
from .models.cms import GeoPage
from django.core.cache import cache
from .tasks import fetch_address_for_point
from wagtail.images.models import Image
from points.serializers import ImageSerializer
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Point)
def get_address_after_create(sender, instance, created, **kwargs):
    if created and not instance.address:
        logger.info(f"Сигнал: запуск геокодирования для точки {instance.id}")
        fetch_address_for_point.delay(instance.id)


@receiver([post_save, post_delete], sender=Image)
def clear_image_cache_on_change(sender, instance, **kwargs):
    logger.info(f"Сигнал: очистка кэша для изображения {instance.id}")
    ImageSerializer.clear_cache()


@receiver([post_save, post_delete], sender=GeoPage)
def clear_geopage_cache(sender, instance, **kwargs):
    logger.info(f"Сигнал: очистка кэша @cache_page")
    cache.delete_pattern('views.decorators.cache.cache_page.*')