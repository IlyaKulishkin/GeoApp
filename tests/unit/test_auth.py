"""
Запуск: docker-compose exec web pytest tests/unit/test_auth.py
"""
import pytest
from django.contrib.gis.geos import Point as GEOSPoint
from rest_framework import status
from points.models.api import Point, Message
from points.models.cms import GeoPage


@pytest.mark.django_db
class TestAuthEndpoints:

    def test_obtain_token_success(self, api_client, admin_user):
        response = api_client.post('/api/auth/token/', {
            'username': 'test_admin',
            'password': 'testpass123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_obtain_token_invalid_credentials(self, api_client):
        response = api_client.post('/api/auth/token/', {
            'username': 'wrong',
            'password': 'wrong'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, auth_token):
        token_resp = api_client.post('/api/auth/token/', {
            'username': 'test_admin',
            'password': 'testpass123'
        })
        refresh = token_resp.data['refresh']

        response = api_client.post('/api/auth/token/refresh/', {'refresh': refresh})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data