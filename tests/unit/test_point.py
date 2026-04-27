"""
Запуск: docker-compose exec web pytest tests/unit/test_point.py
"""
import pytest
from rest_framework import status
from points.models.api import Point


@pytest.mark.django_db
class TestPointEndpoints:

    def test_create_point_success(self, authenticated_client, sample_point_data):
        response = authenticated_client.post('/api/points/', sample_point_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['name'] == sample_point_data['name']
        assert 'id' in response.json()
        assert 'created_at' in response.json()
        assert response.json()['address'] is None

    def test_create_point_address_filled_by_celery(self, authenticated_client, sample_point_data):
        response = authenticated_client.post('/api/points/', sample_point_data)
        assert response.status_code == status.HTTP_201_CREATED
        point_id = response.json()['id']

        point = Point.objects.get(id=point_id)
        assert point.address == 'Тестовый адрес'

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
        # 5. UPDATE "points_point" SET "address" = 'Тестовый адрес'
        # 6. SELECT "points_point"
        # 7. SAVEPOINT
        # 8. SELECT "wagtailcore_referenceindex"
        # 9. INSERT INTO "wagtailcore_referenceindex"
        # 10. RELEASE SAVEPOINT
        # 11. SELECT "points_point"
        # 12. SAVEPOINT
        # 13. SELECT "wagtailcore_referenceindex"
        # 14. RELEASE SAVEPOINT
        with django_assert_num_queries(14):
            response = authenticated_client.post('/api/points/', sample_point_data)

        assert response.status_code == status.HTTP_201_CREATED