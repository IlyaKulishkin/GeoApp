import factory
import random
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point as GEOSPoint
from django.core.files.base import ContentFile
from wagtail.images.models import Image
from wagtail.models import Page
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, Sequence, PostGenerationMethodCall, lazy_attribute
import base64
from faker import Faker

from points.models.api import Point, Message
from points.models.cms import GeoPage, GeoPagePoint

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Фабрика для создания пользователей"""
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = Sequence(lambda n: f'user{n}')
    email = LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True
    is_staff = False
    is_superuser = False


class AdminUserFactory(UserFactory):
    """Фабрика для создания суперпользователя"""
    is_staff = True
    is_superuser = True
    username = Sequence(lambda n: f'admin{n}')


class ImageFactory(DjangoModelFactory):
    """Фабрика для создания тестовых изображений"""
    class Meta:
        model = Image

    title = Sequence(lambda n: f'Test Image {n}')

    @lazy_attribute
    def file(self):
        fake_image = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        return ContentFile(fake_image, name=f'{self.title}.png')

    @factory.post_generation
    def create_renditions(self, create, extracted, **kwargs):
        if create:
            self.get_rendition('original')
            self.get_rendition('max-400x400')


class PointFactory(DjangoModelFactory):
    """Фабрика для создания гео-точек"""
    class Meta:
        model = Point

    name = Sequence(lambda n: f'Test Point {n}')
    address = factory.Faker('address')
    created_by = SubFactory(UserFactory)
    created_at = factory.Faker('date_time_this_year')

    @lazy_attribute
    def location(self):
        return GEOSPoint(
            random.uniform(37.5, 37.7),
            random.uniform(55.7, 55.8),
            srid=4326
        )


class MessageFactory(DjangoModelFactory):
    """Фабрика для создания сообщений"""
    class Meta:
        model = Message

    point = SubFactory(PointFactory)
    author = SubFactory(UserFactory)
    text = factory.Faker('text', max_nb_chars=200)
    created_at = factory.Faker('date_time_this_year')


class GeoPageFactory(DjangoModelFactory):
    """Фабрика для создания GeoPage"""
    class Meta:
        model = GeoPage

    title = Sequence(lambda n: f'Test GeoPage {n}')
    slug = LazyAttribute(lambda obj: f'test-page-{obj.title.lower().replace(" ", "-")[:30]}')
    content = factory.LazyFunction(lambda: [
        ('header', {
            'title': 'Test Header',
            'description': '<p>Test description</p>'
        })
    ])

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = model_class(*args, **kwargs)

        root = Page.objects.first()
        if not root:
            root = Page.add_root(title='Root', slug='root')

        root.add_child(instance=instance)
        instance.save_revision().publish()
        return instance


class GeoPageWithSliderFactory(GeoPageFactory):
    """Фабрика для GeoPage со слайдером"""

    class Params:
        slider_images = None

    @lazy_attribute
    def content(self):
        fake = Faker()

        images = self.slider_images or ImageFactory.create_batch(3)
        return [
            ('header', {
                'title': fake.sentence(),
                'description': f'<p>{fake.paragraph()}</p>'
            }),
            ('slider', {
                'slides': [
                    {'image': img, 'caption': f'Slide {i + 1}'}
                    for i, img in enumerate(images)
                ]
            })
        ]


class GeoPagePointFactory(DjangoModelFactory):
    """Фабрика для связи GeoPage и Point"""
    class Meta:
        model = GeoPagePoint

    page = SubFactory(GeoPageFactory)
    point = SubFactory(PointFactory)