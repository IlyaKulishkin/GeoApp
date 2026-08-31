"""
Запуск: docker-compose exec web pytest tests/unit/test_message.py
"""
import pytest
from rest_framework import status

@pytest.mark.django_db
class TestMessageEndpoints:

    def test_create_message_success(self, authenticated_client, sample_message_data):
        response = authenticated_client.post('/api/points/messages/', sample_message_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['text'] == sample_message_data['text']
        assert 'id' in response.json()

    def test_create_message_invalid_point(self, authenticated_client):
        response = authenticated_client.post('/api/points/messages/', {
            'point_id': 99999,
            'text': 'Test'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'point' in str(response.json()).lower() or 'does not exist' in str(response.json())

    def test_create_message_unauthorized(self, api_client, test_point):
        response = api_client.post('/api/points/messages/', {
            'point_id': test_point.id,
            'text': 'Test'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED