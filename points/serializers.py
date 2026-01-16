from rest_framework import serializers
from .models import Point, Message
from django.contrib.gis.geos import Point as GEOSPoint


class PointSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Point
        fields = ['id', 'name', 'latitude', 'longitude', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lon = validated_data.pop('longitude')
        location = GEOSPoint(lon, lat, srid=4326)
        point = Point.objects.create(location=location, **validated_data)
        return point


class MessageSerializer(serializers.ModelSerializer):
    point_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Message
        fields = ['id', 'point_id', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_point_id(self, value):
        if not Point.objects.filter(id=value).exists():
            raise serializers.ValidationError("Point with this ID does not exist.")
        return value

    def create(self, validated_data):
        point_id = validated_data.pop('point_id')
        point = Point.objects.get(id=point_id)
        message = Message.objects.create(point=point, **validated_data)
        return message
