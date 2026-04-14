"""
Запуск: docker-compose exec web pytest tests/unit/test_search.py
"""
import pytest
from django.contrib.gis.geos import Point as GEOSPoint
from rest_framework import status
from points.models.api import Point, Message
from points.models.cms import GeoPage

@pytest.mark.django_db
class TestSearchEndpoints:

    def test_search_points_success(self, authenticated_client, test_point):
        response = authenticated_client.get('/api/points/search/', {
            'latitude': 55.75,
            'longitude': 37.62,
            'radius': 2
        })
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

        found = next((p for p in response.data if p['id'] == test_point.id), None)
        assert found is not None
        assert 'distance_km' in found
        assert found['distance_km'] < 2.0

    def test_search_points_invalid_params(self, authenticated_client):
        response = authenticated_client.get('/api/points/search/', {
            'latitude': 55.75,
            'longitude': 37.62,
            'radius': -1
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = authenticated_client.get('/api/points/search/', {
            'latitude': 100,
            'longitude': 37.62,
            'radius': 1
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_messages_success(self, authenticated_client, test_point):
        Message.objects.create(
            point=test_point,
            text='Test message',
            author=test_point.created_by
        )

        response = authenticated_client.get('/api/messages/search/', {
            'latitude': 55.75,
            'longitude': 37.62,
            'radius': 2
        })
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        found = next((m for m in response.data if m['text'] == 'Test message'), None)
        assert found is not None
        assert found['point_name'] == test_point.name
        assert found['author_username'] == test_point.created_by.username