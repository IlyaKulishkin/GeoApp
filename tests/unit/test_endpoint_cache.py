"""
Запуск: docker-compose exec web pytest tests/unit/test_endpoint_cache.py
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestPageCaching:

    def test_list_pages_cached(self, authenticated_client, geo_page):
        url = '/api/pages/'

        response_1 = authenticated_client.get(url)
        assert response_1.status_code == status.HTTP_200_OK
        data_1 = response_1.json()

        response_2 = authenticated_client.get(url)
        assert response_2.status_code == status.HTTP_200_OK
        data_2 = response_2.json()

        assert data_1 == data_2

        assert 'Cache-Control' in response_2
        assert 'max-age=2592000' in response_2['Cache-Control']

    def test_detail_page_cached(self, authenticated_client, geo_page):
        url = f'/api/pages/{geo_page.pk}/'

        response_1 = authenticated_client.get(url)
        assert response_1.status_code == status.HTTP_200_OK
        data_1 = response_1.json()

        response_2 = authenticated_client.get(url)
        assert response_2.status_code == status.HTTP_200_OK
        data_2 = response_2.json()

        assert data_1 == data_2
        assert 'Cache-Control' in response_2
        assert 'max-age=2592000' in response_2['Cache-Control']

    def test_list_pages_cache_reduces_queries(self, authenticated_client, geo_page, django_assert_num_queries):
        url = '/api/pages/'

        authenticated_client.get(url)

        with django_assert_num_queries(0):
            response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_detail_page_cache_reduces_queries(self, authenticated_client, geo_page, django_assert_num_queries):
        url = f'/api/pages/{geo_page.pk}/'

        authenticated_client.get(url)

        with django_assert_num_queries(0):
            response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_cache_invalidated_on_update(self, authenticated_client, geo_page, django_assert_num_queries):
        url = '/api/pages/'

        authenticated_client.get(url)

        with django_assert_num_queries(0):
            response_1 = authenticated_client.get(url)
        old_title = response_1.json()['results'][0]['title']

        geo_page.title = 'Новый заголовок'
        geo_page.save_revision().publish()

        # 1. SELECT "auth_user"
        # 2. SELECT COUNT(*)
        # 3. SELECT "wagtailcore_page"
        with django_assert_num_queries(3):
            response_2 = authenticated_client.get(url)

        new_title = response_2.json()['results'][0]['title']
        assert old_title != new_title
        assert new_title == 'Новый заголовок'

    def test_detail_cache_invalidated_on_update(self, authenticated_client, geo_page, django_assert_num_queries):
        url = f'/api/pages/{geo_page.pk}/'

        authenticated_client.get(url)

        with django_assert_num_queries(0):
            response_1 = authenticated_client.get(url)

        geo_page.title = 'Обновлённый заголовок'
        geo_page.save_revision().publish()

        # 1. SELECT "auth_user"
        # 2. SELECT "wagtailcore_page"
        # 3. SELECT "points_geopagepoint"
        # 4. SELECT "wagtailimages_image"
        with django_assert_num_queries(4):
            response_2 = authenticated_client.get(url)

        assert response_2.json()['title'] == 'Обновлённый заголовок'