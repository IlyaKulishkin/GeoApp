import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from wagtail.models import Page
from django.contrib.gis.geos import Point as GEOSPoint

from .factories import (
    UserFactory,
    AdminUserFactory,
    PointFactory,
    MessageFactory,
    ImageFactory,
    GeoPageWithSliderFactory,
    GeoPagePointFactory,
)


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Глобальная настройка БД для тестов"""
    pass


@pytest.fixture
def api_client():
    """Базовый DRF клиент без авторизации"""
    return APIClient()


@pytest.fixture
def user(db):
    """Создаёт обычного пользователя"""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Создаёт суперпользователя"""
    return AdminUserFactory(username='test_admin')


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
    """Создаёт тестовое изображение с рендерами"""
    return ImageFactory()


@pytest.fixture(scope='session')
def slider_images(django_db_setup, django_db_blocker):
    """Создаёт 3 изображения один раз на тесты page"""
    with django_db_blocker.unblock():
        return ImageFactory.create_batch(3)


@pytest.fixture
def geo_page(db, wagtail_root, slider_images):
    """Создаёт и публикует GeoPage со слайдером"""
    return GeoPageWithSliderFactory(
        title='Test page',
        slug='test-page',
        slider_images=slider_images,
    )


@pytest.fixture
def test_point(db, admin_user):
    """Создаёт гео-точку для тестов"""
    return PointFactory(
        created_by=admin_user,
        name='Test Point',
        location=GEOSPoint(37.6173, 55.7558, srid=4326),
        address='Москва, Кремль'
    )


@pytest.fixture
def test_message(db, test_point, admin_user):
    """Создаёт тестовое сообщение (не испрользуется в тестах, реализовал в рамках ознакомления с factory boy)"""
    return MessageFactory(
        point=test_point,
        author=admin_user,
        text='Test message'
    )


@pytest.fixture
def linked_point(db, geo_page, test_point):
    """Привязывает точку к странице через GeoPagePoint"""
    return GeoPagePointFactory(page=geo_page, point=test_point)


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


@pytest.fixture
def sample_search_data():
    """Данные для поиска"""
    return {
        'latitude': 55.75,
        'longitude': 37.62,
        'radius': 2
    }


@pytest.fixture(autouse=True)
def celery_always_eager(settings):
    """Запускает Celery задачи синхронно в тестах"""
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.fixture(autouse=True)
def mock_dadata(monkeypatch):
    """Мокает DadataService"""
    def mock_get_address(self, lat, lon, radius_meters=100):
        return f"Тестовый адрес"

    monkeypatch.setattr(
        'points.services.dadata_service.DadataService.get_address_by_coordinates',
        mock_get_address
    )


@pytest.fixture(autouse=True)
def clear_redis_test_db(settings):
    """Использует отдельную базу Redis для тестов и очищает её после"""
    settings.CACHES['default']['LOCATION'] = 'redis://redis:6379/9'

    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()