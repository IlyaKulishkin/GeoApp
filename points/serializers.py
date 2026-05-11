from rest_framework import serializers, exceptions
from .models.api import Point, Message
from .services.point_service import create_point, PointValidationError
from .services.message_service import create_message
from .models.cms import GeoPage, GeoPagePoint
from wagtail.images.models import Image

class MessagePointSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'text', 'created_at', 'author_name']
        read_only_fields = fields

class PointSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Point
        fields = ['id', 'name', 'address', 'latitude', 'longitude', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lon = validated_data.pop('longitude')
        user = self.context['request'].user
        try:
            return create_point(
                name=validated_data['name'],
                latitude=lat,
                longitude=lon,
                user=user
            )
        except PointValidationError as e:
            raise serializers.ValidationError({e.field: [e.message]})

class MessageSerializer(serializers.ModelSerializer):
    point_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Message
        fields = ['id', 'point_id', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        point_id = validated_data.pop('point_id')
        author = self.context['request'].user
        try:
            return create_message(
                point_id=point_id,
                text=validated_data['text'],
                author=author
            )
        except ValueError as e:
            raise serializers.ValidationError({'point_id': str(e)})

class ImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    _cache = {}

    class Meta:
        model = Image
        fields = ['id', 'title', 'url', 'thumbnail_url', 'width', 'height']

    def to_representation(self, instance):
        cache_key = f"img_{instance.id}"

        if cache_key not in self._cache:
            self._cache[cache_key] = super().to_representation(instance)

        return self._cache[cache_key]

    def get_url(self, obj):
        try:
            return obj.get_rendition('original').url
        except Exception:
            return None

    def get_thumbnail_url(self, obj):
        try:
            return obj.get_rendition('max-400x400').url
        except Exception:
            return None

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    @classmethod
    def get_cache_size(cls):
        return len(cls._cache)


class GeoPagePointSerializer(serializers.ModelSerializer):
    point_name = serializers.CharField(source='point.name', read_only=True)
    point_address = serializers.CharField(source='point.address', read_only=True)
    point_latitude = serializers.SerializerMethodField()
    point_longitude = serializers.SerializerMethodField()
    messages = MessagePointSerializer(many=True, read_only=True, source="point.authored_messages_points")

    class Meta:
        model = GeoPagePoint
        fields = ['id', 'point_name', 'point_address', 'point_latitude', 'point_longitude', 'messages']

    def get_point_latitude(self, obj):
        return obj.point.location.y if obj.point.location else None

    def get_point_longitude(self, obj):
        return obj.point.location.x if obj.point.location else None


class GeoPageListSerializer(serializers.ModelSerializer):
    page_url = serializers.URLField(source='get_full_url', read_only=True)

    class Meta:
        model = GeoPage
        fields = ['id', 'title', 'first_published_at', 'last_published_at', 'live', 'page_url']


class SliderBlockSerializer(serializers.Serializer):
    slides = serializers.SerializerMethodField()

    def get_slides(self, block_value):
        raw_slides = block_value.get('slides', [])
        return [
            {
                'caption': slide.get('caption', ''),
                'image': ImageSerializer(slide.get('image')).data
            }
            for slide in raw_slides
        ]


class HeaderBlockSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.SerializerMethodField()

    def get_description(self, block_value):
        desc = block_value.get('description', '')
        return str(desc) if desc else ''


class BlockSerializerRegistry:
    _registry = {
        'slider': SliderBlockSerializer,
        'header': HeaderBlockSerializer,
    }

    @classmethod
    def get_serializer(cls, block_type):
        return cls._registry.get(block_type)

    @classmethod
    def register(cls, block_type):
        def decorator(serializer_cls):
            cls._registry[block_type] = serializer_cls
            return serializer_cls
        return decorator


class GeoPageDetailSerializer(serializers.ModelSerializer):
    page_url = serializers.URLField(source='get_full_url', read_only=True)
    points = GeoPagePointSerializer(source='page_points', many=True, read_only=True)
    content_blocks = serializers.SerializerMethodField()

    class Meta:
        model = GeoPage
        fields = [
            'id', 'title', 'slug', 'content_blocks',
            'points', 'page_url', 'first_published_at', 'last_published_at', 'live'
        ]


    def get_content_blocks(self, obj):
        if not obj.content:
            return []

        result = []
        for block in obj.content:
            serializer_cls = BlockSerializerRegistry.get_serializer(block.block_type)

            if serializer_cls:
                block_data = serializer_cls(block.value).data
            else:
                block_data = {'raw': str(block.value)}

            result.append({
                'type': block.block_type,
                'id': block.id,
                'value': block_data
            })
        return result