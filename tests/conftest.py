import pytest
import os
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point as GEOSPoint
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from wagtail.models import Page, Site
from wagtail.images.models import Image

from points.models.api import Point, Message
from points.models.cms import GeoPage, GeoPagePoint


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Глобальная настройка БД для тестов"""
    pass


@pytest.fixture
def api_client():
    """Базовый DRF клиент без авторизации"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Создаёт тестового суперпользователя"""
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username='test_admin',
        defaults={'email': 'test@admin.com', 'is_superuser': True}
    )
    user.set_password('testpass123')
    user.save()
    return user


@pytest.fixture
def auth_token(admin_user):
    """Генерирует JWT access-токен для тестового пользователя"""
    refresh = RefreshToken.for_user(admin_user)
    return str(refresh.access_token)


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """DRF клиент с авторизацией через Bearer-токен"""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
    return api_client


@pytest.fixture
def wagtail_root(db):
    """Возвращает корневую страницу Wagtail"""
    root = Page.objects.first()
    if not root:
        root = Page.add_root(title='Root', slug='root')
    return root


@pytest.fixture
def dummy_image(db):
    """Создаёт тестовое изображение"""
    file = BytesIO()
    img = PILImage.new('RGB', (100, 100), color='blue')
    img.save(file, 'jpeg')
    file.name = 'test_img.jpg'
    file.seek(0)

    django_file = SimpleUploadedFile(
        name='test_img.jpg',
        content=file.read(),
        content_type='image/jpeg'
    )
    return Image.objects.create(title='Test Image', file=django_file)


@pytest.fixture
def geo_page(db, wagtail_root, dummy_image):
    """Создаёт и публикует GeoPage с контентом для тестов"""
    page = GeoPage(
        title='Тестовая страница',
        slug='test-page',
        content=[
            ('header', {
                'title': 'Главный заголовок',
                'description': '<p>Описание с <strong>жирным</strong> текстом</p>'
            }),
            ('slider', {
                'slides': [
                    {'image': dummy_image, 'caption': 'Слайд 1'},
                    {'image': dummy_image, 'caption': 'Слайд 2'},
                    {'image': dummy_image, 'caption': 'Слайд 3'},
                ]
            })
        ]
    )
    wagtail_root.add_child(instance=page)
    page.save_revision().publish()
    return page


@pytest.fixture
def test_point(db, admin_user):
    """Создаёт гео-точку для тестов"""
    return Point.objects.create(
        name='Test Point',
        location=GEOSPoint(37.6173, 55.7558, srid=4326),
        address='Москва, Кремль',
        created_by=admin_user
    )


@pytest.fixture
def linked_point(db, geo_page, test_point):
    """Привязывает точку к странице через GeoPagePoint"""
    return GeoPagePoint.objects.create(page=geo_page, point=test_point)


@pytest.fixture
def sample_point_data():
    """Данные для создания точки"""
    return {
        'name': 'Sample Point',
        'latitude': 55.7558,
        'longitude': 37.6173
    }


@pytest.fixture
def sample_message_data(test_point):
    """Данные для создания сообщения"""
    return {
        'point_id': test_point.id,
        'text': 'Sample message text'
    }