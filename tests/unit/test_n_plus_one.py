"""
Запуск: docker-compose exec web pytest tests/unit/test_n_plus_one.py -s
"""
import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.core.cache import cache
from points.models.cms import GeoPage
from points.serializers import GeoPageDetailSerializer
from tests.factories import PointFactory, GeoPagePointFactory, MessageFactory


@pytest.mark.django_db
class TestNPlusOne:

    def test_without_message_prefetch(self, geo_page, test_point):
        cache.clear()

        for i in range(5):
            point = PointFactory(created_by=test_point.created_by)
            GeoPagePointFactory(page=geo_page, point=point)
            MessageFactory(point=point, author=test_point.created_by)

        with CaptureQueriesContext(connection) as queries:
            qs = GeoPage.objects.filter(id=geo_page.id).prefetch_related('page_points__point')
            page = qs.first()
            serializer = GeoPageDetailSerializer(page)
            data = serializer.data

            print(f"Запросов без prefetch сообщений: {len(queries)}")

            message_queries = [q for q in queries if 'SELECT' in q['sql'] and 'message' in q['sql'].lower()]
            print(f"Запросов к message: {len(message_queries)}")

    def test_with_message_prefetch(self, geo_page, test_point):
        cache.clear()

        for i in range(5):
            point = PointFactory(created_by=test_point.created_by)
            GeoPagePointFactory(page=geo_page, point=point)
            MessageFactory(point=point, author=test_point.created_by)

        with CaptureQueriesContext(connection) as queries:
            qs = GeoPage.objects.filter(id=geo_page.id).prefetch_related(
            'page_points__point__authored_messages_points__author'
            )
            page = qs.first()
            serializer = GeoPageDetailSerializer(page)
            data = serializer.data

            print(f"\nЗапросов с prefetch сообщений: {len(queries)}")

            message_queries = [q for q in queries if 'SELECT' in q['sql'] and 'message' in q['sql'].lower()]
            print(f"Запросов к message: {len(message_queries)}")