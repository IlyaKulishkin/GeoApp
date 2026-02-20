from rest_framework import serializers
from .models.api import Point, Message
from .services.point_service import create_point
from .services.message_service import create_message

class PointSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Point
        fields = ['id', 'name', 'latitude', 'longitude', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lon = validated_data.pop('longitude')
        user = self.context['request'].user
        return create_point(
            name=validated_data['name'],
            latitude=lat,
            longitude=lon,
            user=user
        )

class MessageSerializer(serializers.ModelSerializer):
    point_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Message
        fields = ['id', 'point_id', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        point_id = validated_data.pop('point_id')
        author = self.context['request'].user
        return create_message(
            point_id=point_id,
            text=validated_data['text'],
            author=author
        )