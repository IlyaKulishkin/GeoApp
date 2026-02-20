from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point as GEOSPoint
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models.api import Point, Message
from .serializers import PointSerializer, MessageSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter


def validate_geo_params(lat, lon, radius):
    try:
        lat = float(lat)
        lon = float(lon)
        radius = float(radius)
    except (TypeError, ValueError):
        raise ValueError("Latitude, longitude and radius must be numbers.")

    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180.")
    if radius <= 0:
        raise ValueError("Radius must be greater than 0.")

    return lat, lon, radius


class PointCreateView(generics.CreateAPIView):
    queryset = Point.objects.all()
    serializer_class = PointSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@extend_schema(
    summary="Поиск точек в радиусе",
    parameters=[
        OpenApiParameter(name='latitude', type=float, required=True, description='Широта центра (например, 55.75)'),
        OpenApiParameter(name='longitude', type=float, required=True, description='Долгота центра (например, 37.62)'),
        OpenApiParameter(name='radius', type=float, default=1.0, description='Радиус поиска в километрах'),
    ]
)
@api_view(['GET'])
def search_points(request):
    """
    GET /api/points/search/?latitude=55.75&longitude=37.62&radius=2
    radius — в километрах
    """
    try:
        lat = request.GET.get('latitude')
        lon = request.GET.get('longitude')
        radius_km = request.GET.get('radius', 1)

        lat, lon, radius_km = validate_geo_params(lat, lon, radius_km)
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_location = GEOSPoint(lon, lat, srid=4326)
    radius_m = radius_km * 1000

    points = Point.objects.filter(
        location__distance_lte=(user_location, radius_m)
    ).annotate(
        distance=Distance('location', user_location)
    ).order_by('distance')

    serializer = PointSerializer(points, many=True)
    data = []
    for point, item in zip(points, serializer.data):
        item['distance_km'] = round(point.distance.km, 3)
        data.append(item)

    return Response(data)


@extend_schema(
    summary="Поиск сообщений в точках в радиусе",
    parameters=[
        OpenApiParameter(name='latitude', type=float, required=True, description='Широта центра (например, 55.75)'),
        OpenApiParameter(name='longitude', type=float, required=True, description='Долгота центра (например, 37.62)'),
        OpenApiParameter(name='radius', type=float, default=1.0, description='Радиус поиска в километрах'),
    ]
)
@api_view(['GET'])
def search_messages(request):
    """
    GET /api/messages/search/?latitude=55.75&longitude=37.62&radius=2
    Возвращает все сообщения в точках, находящихся в радиусе.
    """
    try:
        lat = request.GET.get('latitude')
        lon = request.GET.get('longitude')
        radius_km = request.GET.get('radius', 1)

        lat, lon, radius_km = validate_geo_params(lat, lon, radius_km)
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    user_location = GEOSPoint(lon, lat, srid=4326)
    radius_m = radius_km * 1000

    nearby_points = Point.objects.filter(
        location__distance_lte=(user_location, radius_m)
    )

    messages = Message.objects.filter(
        point__in=nearby_points
    ).select_related('point', 'author').order_by('-created_at')

    result = []
    for msg in messages:
        data = {
            "id": msg.id,
            "text": msg.text,
            "created_at": msg.created_at,
            "point_name": msg.point.name,
            "point_latitude": msg.point.location.y,
            "point_longitude": msg.point.location.x,
            "author_username": msg.author.username,
        }
        result.append(data)

    return Response(result)
