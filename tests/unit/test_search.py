"""
Запуск: docker-compose exec web pytest tests/unit/test_search.py
"""
import pytest
from rest_framework import status
from points.models.api import Message

@pytest.mark.django_db
class TestSearchEndpoints:

    def test_search_points_success(self, authenticated_client, test_point, sample_search_data):
        response = authenticated_client.get('/api/points/search/', sample_search_data)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

        found = next((p for p in response.json() if p['id'] == test_point.id), None)
        assert found is not None
        assert 'distance_km' in found
        assert found['distance_km'] < 2.0

    @pytest.mark.parametrize('params,expected_error_substring', [
        ({'latitude': 55.75, 'longitude': 37.62, 'radius': -1}, 'radius'),

        ({'latitude': -91, 'longitude': 37.62, 'radius': 1}, 'latitude'),
        ({'latitude': 91, 'longitude': 37.62, 'radius': 1}, 'latitude'),

        ({'latitude': 55.75, 'longitude': -181, 'radius': 1}, 'longitude'),
        ({'latitude': 55.75, 'longitude': 181, 'radius': 1}, 'longitude'),

        ({'latitude': 'abc', 'longitude': 37.62, 'radius': 1}, 'numbers'),
        ({'latitude': 55.75, 'longitude': 'def', 'radius': 1}, 'numbers'),
        ({'latitude': 55.75, 'longitude': 37.62, 'radius': 'ghi'}, 'numbers'),

        ({'longitude': 37.62, 'radius': 1}, 'latitude'),
        ({'latitude': 55.75, 'radius': 1}, 'longitude'),

        ({'latitude': '', 'longitude': 37.62, 'radius': 1}, 'latitude'),
        ({'latitude': 55.75, 'longitude': '', 'radius': 1}, 'longitude'),
        ({'latitude': 55.75, 'longitude': 37.62, 'radius': ''}, 'radius'),
    ])
    def test_search_points_invalid_params(self, authenticated_client, params, expected_error_substring):
        response = authenticated_client.get('/api/points/search/', params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_message = response.json()['error'].lower()
        assert expected_error_substring in error_message, f"Expected '{expected_error_substring}' in error message: {error_message}"

    def test_search_messages_success(self, authenticated_client, test_point, sample_search_data):
        Message.objects.create(
            point=test_point,
            text='Test message',
            author=test_point.created_by
        )

        response = authenticated_client.get('/api/messages/search/', sample_search_data)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

        found = next((m for m in response.json() if m['text'] == 'Test message'), None)
        assert found is not None
        assert found['point_name'] == test_point.name
        assert found['author_username'] == test_point.created_by.username

    def test_search_points_query_count(self, authenticated_client, test_point, django_assert_num_queries, sample_search_data):
        # 1 SELECT auth_user
        # 2 SELECT points_point
        with django_assert_num_queries(2):
            response = authenticated_client.get('/api/points/search/', sample_search_data)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1