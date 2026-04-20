"""
Запуск: docker-compose exec web pytest tests/unit/test_point.py
"""
import pytest
from rest_framework import status
from tests.conftest import sample_point_data


@pytest.mark.django_db
class TestPointEndpoints:

    def test_create_point_success(self, authenticated_client, sample_point_data):
        response = authenticated_client.post('/api/points/', sample_point_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['name'] == sample_point_data['name']
        assert 'id' in response.json()
        assert 'created_at' in response.json()
        assert response.json()['address'] is None

    def test_create_point_unauthorized(self, api_client, sample_point_data):
        response = api_client.post('/api/points/', sample_point_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize("params, expected_field", [
        ({'name': 'Invalid', 'latitude': 91, 'longitude': 37.0}, 'latitude'),
        ({'name': 'Invalid', 'latitude': -91, 'longitude': 37.0}, 'latitude'),
        ({'name': 'Invalid', 'latitude': 55.0, 'longitude': -181}, 'longitude'),
        ({'name': 'Invalid', 'latitude': 55.0, 'longitude': 181}, 'longitude'),
    ])
    def test_create_point_invalid_coordinates(self, authenticated_client, params, expected_field):
        response = authenticated_client.post('/api/points/', params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_field in response.json()

    def test_create_point_duplicate_location(self, authenticated_client, test_point):
        response = authenticated_client.post('/api/points/', {
            'name': 'Duplicate',
            'latitude': 55.7558,
            'longitude': 37.6173
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'location' in response.json()

    def test_create_point_query_count(self, authenticated_client, django_assert_num_queries, sample_point_data):
        # 1. SELECT "auth_user"
        # 2. SELECT ... - проверка дубликата
        # 3. INSERT INTO "points_point"
        # 4. SELECT "points_point"
        # 5. SAVEPOINT
        # 6. SELECT "wagtailcore_referenceindex"
        # 7. INSERT INTO "wagtailcore_referenceindex"
        # 8. RELEASE SAVEPOINT
        with django_assert_num_queries(8):
            response = authenticated_client.post('/api/points/', sample_point_data)

        assert response.status_code == status.HTTP_201_CREATED