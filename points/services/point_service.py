from django.contrib.gis.geos import Point as GEOSPoint
from ..models.api import Point
import logging
logger = logging.getLogger(__name__)

class PointValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)

def create_point(*, name: str, latitude: float, longitude: float, user) -> Point:
    """Создаёт геоточку с валидацией координат."""
    if not (-90 <= latitude <= 90):
        raise PointValidationError('latitude', 'Latitude must be between -90 and 90.')
    if not (-180 <= longitude <= 180):
        raise PointValidationError('longitude','Longitude must be between -180 and 180.')
    
    location = GEOSPoint(longitude, latitude, srid=4326)

    if Point.objects.filter(location=location).exists():
        raise PointValidationError('location', 'A point already exists at these coordinates.')
    
    point = Point.objects.create(
        name=name,
        location=location,
        created_by=user
    )

    logger.info(f"Создана точка ID={point.id}. Сигнал запустит геокодирование.")

    return point