"""
Запуск: docker-compose exec web pytest tests/unit/test_image_cache.py
"""
import pytest
from points.serializers import ImageSerializer


@pytest.mark.django_db
class TestImageCache:

    def test_image_cache_works(self, dummy_image):
        data1 = ImageSerializer(dummy_image).data
        data2 = ImageSerializer(dummy_image).data

        assert data1 == data2
        assert ImageSerializer.get_cache_size() > 0

    def test_image_cache_clears(self, dummy_image):
        ImageSerializer(dummy_image).data
        assert ImageSerializer.get_cache_size() > 0

        ImageSerializer.clear_cache()
        assert ImageSerializer.get_cache_size() == 0

    def test_signal_clears_cache(self, dummy_image):
        ImageSerializer(dummy_image).data
        assert ImageSerializer.get_cache_size() > 0

        dummy_image.title = "New Title"
        dummy_image.save()

        assert ImageSerializer.get_cache_size() == 0