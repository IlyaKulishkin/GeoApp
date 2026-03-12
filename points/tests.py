from unittest.mock import patch
from django.test import TestCase
from django.contrib.gis.geos import Point as GEOSPoint
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from points.models.api import Point, Message


class GeoAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_create_point_success(self):
        """Тест создания точки с валидными координатами"""
        with patch('points.tasks.fetch_address_for_point.delay') as mock_task:
            response = self.client.post('/api/points/', {
                'name': 'Red Square',
                'latitude': 55.7539,
                'longitude': 37.6208
            })

            # Проверяем вызов асинхронной задачи
            mock_task.assert_called_once()
            point_id = mock_task.call_args[0][0]

            # Проверяем ответ API
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['name'], 'Red Square')
            self.assertEqual(response.data['address'], None)  # Адрес ещё не заполнен (асинхронно)
            self.assertIn('id', response.data)
            self.assertIn('created_at', response.data)

            # Проверяем, что точка создана в БД
            self.assertEqual(Point.objects.count(), 1)
            point = Point.objects.get(id=response.data['id'])
            self.assertAlmostEqual(point.location.x, 37.6208)
            self.assertAlmostEqual(point.location.y, 55.7539)
            self.assertEqual(point.created_by, self.user)

    def test_create_point_invalid_coordinates(self):
        """Тест валидации координат (широта/долгота)"""
        # Неверная широта (>90)
        response = self.client.post('/api/points/', {
            'name': 'Invalid Point',
            'latitude': 100,
            'longitude': 37.6208
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('latitude', response.data)

        # Неверная долгота (< -180)
        response = self.client.post('/api/points/', {
            'name': 'Invalid Point',
            'latitude': 55.7539,
            'longitude': -200
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('longitude', response.data)

    def test_search_points_with_distance(self):
        """Тест поиска точек в радиусе с расчётом расстояния"""
        Point.objects.create(
            name='Moscow Center',
            location=GEOSPoint(37.6208, 55.7539, srid=4326),
            address='г Москва, Красная площадь',
            created_by=self.user
        )

        response = self.client.get('/api/points/search/', {
            'latitude': 55.75,
            'longitude': 37.62,
            'radius': 2  # км
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        point_data = response.data[0]
        self.assertEqual(point_data['name'], 'Moscow Center')
        self.assertEqual(point_data['address'], 'г Москва, Красная площадь')
        self.assertIn('distance_km', point_data)
        self.assertLess(point_data['distance_km'], 2.0)  # Должно быть в радиусе

    def test_search_points_invalid_params(self):
        """Тест валидации параметров поиска"""
        # Отрицательный радиус
        response = self.client.get('/api/points/search/', {
            'latitude': 55.75,
            'longitude': 37.62,
            'radius': -1
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('radius', response.data)

    def test_create_and_search_messages(self):
        """Тест создания и поиска сообщений"""
        point = Point.objects.create(
            name='Test Point',
            location=GEOSPoint(0, 0, srid=4326),
            address='Test Address',
            created_by=self.user
        )

        # Создаём сообщение
        response = self.client.post('/api/points/messages/', {
            'point_id': point.id,
            'text': 'Hello from the center of the world!'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.count(), 1)

        # Ищем сообщения в радиусе
        response = self.client.get('/api/messages/search/', {
            'latitude': 0.0001,
            'longitude': 0.0001,
            'radius': 0.1  # км
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        msg_data = response.data[0]
        self.assertEqual(msg_data['text'], 'Hello from the center of the world!')
        self.assertEqual(msg_data['point_name'], 'Test Point')
        self.assertEqual(msg_data['point_latitude'], 0.0)
        self.assertEqual(msg_data['point_longitude'], 0.0)
        self.assertEqual(msg_data['author_username'], 'testuser')
        self.assertIn('distance_km', msg_data)

    def test_point_serializer_fields(self):
        """Тест структуры сериализатора (write_only/read_only поля)"""
        point = Point.objects.create(
            name='Test Point',
            location=GEOSPoint(37.62, 55.75, srid=4326),
            address='г Москва, Тверская ул',
            created_by=self.user
        )

        response = self.client.get(f'/api/points/search/?latitude=55.75&longitude=37.62&radius=1')

        self.assertEqual(response.status_code, 200)
        point_data = response.data[0]

        # Поля, которые ДОЛЖНЫ быть в ответе
        self.assertIn('id', point_data)
        self.assertIn('name', point_data)
        self.assertIn('address', point_data)
        self.assertIn('created_at', point_data)
        self.assertIn('distance_km', point_data)

        # Поля, которых НЕ ДОЛЖНО быть (write_only)
        self.assertNotIn('latitude', point_data)
        self.assertNotIn('longitude', point_data)

    @patch('points.tasks.fetch_address_for_point.delay')
    def test_task_called_on_point_creation(self, mock_task):
        """Тест вызова задачи при создании точки через API"""
        self.client.post('/api/points/', {
            'name': 'Test Point',
            'latitude': 51.665984,
            'longitude': 39.212326
        })

        # Задача должна быть вызвана один раз
        mock_task.assert_called_once()
        # Проверяем, что передан корректный ID точки
        args, kwargs = mock_task.call_args
        self.assertIsInstance(args[0], int)