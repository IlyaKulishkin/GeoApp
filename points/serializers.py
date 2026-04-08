from rest_framework import serializers
from .models.api import Point, Message
from .services.point_service import create_point
from .services.message_service import create_message
from .models.cms import GeoPage, GeoPagePoint
from wagtail.images.models import Image

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

class ImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'title', 'url', 'thumbnail_url', 'width', 'height']

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


class GeoPagePointSerializer(serializers.ModelSerializer):
    point_name = serializers.CharField(source='point.name', read_only=True)
    point_address = serializers.CharField(source='point.address', read_only=True)
    point_latitude = serializers.SerializerMethodField()
    point_longitude = serializers.SerializerMethodField()

    class Meta:
        model = GeoPagePoint
        fields = ['id', 'point_name', 'point_address', 'point_latitude', 'point_longitude']

    def get_point_latitude(self, obj):
        return obj.point.location.y if obj.point.location else None

    def get_point_longitude(self, obj):
        return obj.point.location.x if obj.point.location else None


class GeoPageListSerializer(serializers.ModelSerializer):
    page_url = serializers.SerializerMethodField()

    class Meta:
        model = GeoPage
        fields = ['id', 'title', 'first_published_at', 'last_published_at', 'live', 'page_url']

    def get_page_url(self, obj):
        return obj.get_full_url()


class GeoPageDetailSerializer(serializers.ModelSerializer):
    page_url = serializers.SerializerMethodField()
    points = GeoPagePointSerializer(source='page_points', many=True, read_only=True)
    content_blocks = serializers.SerializerMethodField()

    class Meta:
        model = GeoPage
        fields = [
            'id', 'title', 'slug', 'content_blocks',
            'points', 'page_url', 'first_published_at', 'last_published_at', 'live'
        ]

    def get_page_url(self, obj):
        return obj.get_full_url()

    def get_content_blocks(self, obj):
        if not obj.content:
            return []

        result = []
        for block in obj.content:
            block_data = {'type': block.block_type, 'id': block.id, 'value': None}

            if block.block_type == 'slider':
                slides_val = block.value.get('slides', [])
                slides = []
                for slide in slides_val:
                    slide_data = {'caption': slide.get('caption', ''), 'image': None}
                    img = slide.get('image')
                    if img:
                        slide_data['image'] = ImageSerializer(img).data
                    slides.append(slide_data)
                block_data['value'] = {'slides': slides}

            elif block.block_type == 'header':
                h = block.value
                block_data['value'] = {
                    'title': h.get('title', ''),
                    'description': str(h.get('description', ''))
                }

            result.append(block_data)
        return result