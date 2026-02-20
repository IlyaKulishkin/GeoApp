from django.contrib.gis.geos import Point as GEOSPoint
from ..models.api import Point

def create_point(*, name: str, latitude: float, longitude: float, user) -> Point:
    """Создаёт геоточку с валидацией координат."""
    if not (-90 <= latitude <= 90):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180 <= longitude <= 180):
        raise ValueError("Longitude must be between -180 and 180.")
    
    location = GEOSPoint(longitude, latitude, srid=4326)

    if Point.objects.filter(location=location).exists():
        raise ValueError("A point already exists at these coordinates.")
    
    return Point.objects.create(
        name=name,
        location=location,
        created_by=user
    )