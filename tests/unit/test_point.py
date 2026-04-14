"""
Запуск: docker-compose exec web pytest tests/unit/test_point.py
"""
import pytest
from django.contrib.gis.geos import Point as GEOSPoint
from rest_framework import status
from points.models.api import Point, Message
from points.models.cms import GeoPage
from tests.conftest import sample_point_data


@pytest.mark.django_db
class TestPointEndpoints:

    def test_create_point_success(self, authenticated_client, sample_point_data):
        response = authenticated_client.post('/api/points/', sample_point_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == sample_point_data['name']
        assert 'id' in response.data
        assert 'created_at' in response.data
        assert response.data['address'] is None

    def test_create_point_unauthorized(self, api_client):
        response = api_client.post('/api/points/', {
            'name': 'Test',
            'latitude': 55.0,
            'longitude': 37.0
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_point_invalid_coordinates(self, authenticated_client):
        response = authenticated_client.post('/api/points/', {
            'name': 'Invalid',
            'latitude': 100,
            'longitude': 37.0
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'latitude' in response.data

        response = authenticated_client.post('/api/points/', {
            'name': 'Invalid',
            'latitude': 55.0,
            'longitude': -200
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'longitude' in response.data

    def test_create_point_duplicate_location(self, authenticated_client, test_point):
        response = authenticated_client.post('/api/points/', {
            'name': 'Duplicate',
            'latitude': 55.7558,
            'longitude': 37.6173
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'location' in response.data