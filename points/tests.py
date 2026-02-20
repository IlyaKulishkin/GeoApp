from django.test import TestCase
from django.contrib.gis.geos import Point as GEOSPoint
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models.api import Point, Message


class GeoAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_create_point(self):
        response = self.client.post('/api/points/', {
            'name': 'Red Square',
            'latitude': 55.7539,
            'longitude': 37.6208
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Point.objects.count(), 1)

    def test_search_points(self):
        Point.objects.create(
            name='Moscow',
            location=GEOSPoint(37.6208, 55.7539, srid=4326),
            created_by=self.user
        )
        response = self.client.get('/api/points/search/', {
            'latitude': 55.75,
            'longitude': 37.62,
            'radius': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn('distance_km', response.data[0])

    def test_create_and_search_messages(self):
        point = Point.objects.create(
            name='Test Point',
            location=GEOSPoint(0, 0, srid=4326),
            created_by=self.user
        )
        self.client.post('/api/points/messages/', {
            'point_id': point.id,
            'text': 'Hello from the center of the world!'
        })
        response = self.client.get('/api/messages/search/', {
            'latitude': 0.0001,
            'longitude': 0.0001,
            'radius': 0.1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['text'], 'Hello from the center of the world!')
