"""
Запуск: docker-compose exec web pytest tests/unit/test_message.py
"""
import pytest
from django.contrib.gis.geos import Point as GEOSPoint
from rest_framework import status
from points.models.api import Point, Message
from points.models.cms import GeoPage

@pytest.mark.django_db
class TestMessageEndpoints:

    def test_create_message_success(self, authenticated_client, test_point):
        response = authenticated_client.post('/api/points/messages/', {
            'point_id': test_point.id,
            'text': 'Hello from test!'
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['text'] == 'Hello from test!'
        assert 'id' in response.data

    def test_create_message_invalid_point(self, authenticated_client):
        response = authenticated_client.post('/api/points/messages/', {
            'point_id': 99999,
            'text': 'Test'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'point' in str(response.data).lower() or 'does not exist' in str(response.data)

    def test_create_message_unauthorized(self, api_client, test_point):
        response = api_client.post('/api/points/messages/', {
            'point_id': test_point.id,
            'text': 'Test'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED