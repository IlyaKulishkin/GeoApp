"""
Запуск: docker-compose exec web pytest tests/unit/test_page.py
"""
import pytest
from django.contrib.gis.geos import Point as GEOSPoint
from rest_framework import status
from points.models.api import Point, Message
from points.models.cms import GeoPage

@pytest.mark.django_db
class TestGeoPageEndpoints:

    def test_list_pages_unauthorized(self, api_client):
        response = api_client.get('/api/pages/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_pages_empty(self, authenticated_client):
        response = authenticated_client.get('/api/pages/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 0
        assert response.json()['results'] == []
        assert response.json()['next'] is None
        assert response.json()['previous'] is None

    def test_list_pages_returns_published(self, authenticated_client, geo_page):
        response = authenticated_client.get('/api/pages/')
        assert response.status_code == 200

        assert response.json()['count'] == 1
        assert len(response.json()['results']) == 1

        page_data = response.json()['results'][0]
        assert page_data['id'] == geo_page.pk
        assert page_data['title'] == geo_page.title
        assert 'page_url' in page_data

        assert 'content_blocks' not in page_data
        assert 'points' not in page_data

    def test_detail_page_unauthorized(self, api_client, geo_page):
        response = api_client.get(f'/api/pages/{geo_page.pk}/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_page_not_found(self, authenticated_client):
        response = authenticated_client.get('/api/pages/99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_page_basic_fields(self, authenticated_client, geo_page):
        response = authenticated_client.get(f'/api/pages/{geo_page.pk}/')
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data['slug'] == geo_page.slug
        assert data['live'] is True
        assert data['page_url'] is None

    def test_detail_page_content_blocks_structure(self, authenticated_client, geo_page):
        response = authenticated_client.get(f'/api/pages/{geo_page.pk}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        blocks = data['content_blocks']

        assert isinstance(blocks, list)
        assert len(blocks) == 2

        header = blocks[0]
        assert header['type'] == 'header'
        assert 'title' in header['value']
        assert 'description' in header['value']

        slider = blocks[1]
        assert slider['type'] == 'slider'
        assert len(slider['value']['slides']) == 3

        slide = slider['value']['slides'][0]
        assert 'caption' in slide
        assert 'image' in slide
        assert 'url' in slide['image']
        assert 'thumbnail_url' in slide['image']

    def test_detail_page_linked_points(self, authenticated_client, linked_point):
        response = authenticated_client.get(f'/api/pages/{linked_point.page.pk}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'points' in data
        assert len(data['points']) == 1

        pt = data['points'][0]
        assert pt['point_name'] == 'Test Point'
        assert pt['point_address'] == 'Москва, Кремль'
        assert pt['point_latitude'] == 55.7558
        assert pt['point_longitude'] == 37.6173

    def test_detail_page_excludes_drafts(self, authenticated_client, wagtail_root):
        draft = GeoPage(title='Draft', slug='draft', live=False)
        wagtail_root.add_child(instance=draft)
        draft.save()

        response = authenticated_client.get(f'/api/pages/{draft.pk}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_page_queries(self, authenticated_client, linked_point, django_assert_num_queries):
        # 1. SELECT auth_user
        # 2. SELECT wagtailcore_page
        # 3. SELECT points_geopagepoint
        # 4. SELECT points_point
        # 5. SELECT wagtailimages_image
        with django_assert_num_queries(5):
            response = authenticated_client.get(f'/api/pages/{linked_point.page.pk}/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['points']) == 1