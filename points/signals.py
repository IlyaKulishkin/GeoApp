from django.db.models.signals import post_save
from django.dispatch import receiver
from .models.api import Point
from .tasks import fetch_address_for_point
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Point)
def get_address_after_create(sender, instance, created, **kwargs):
    if created and not instance.address:
        logger.info(f"Сигнал: запуск геокодирования для точки {instance.id}")
        fetch_address_for_point.delay(instance.id)