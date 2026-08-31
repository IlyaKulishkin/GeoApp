from django.contrib.gis.db import models
from wagtail.models import Page, Orderable
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey

from points.blocks import SliderBlock, HeaderBlock


class GeoPagePoint(Orderable):
    page = ParentalKey('GeoPage', on_delete=models.CASCADE, related_name='page_points')
    point = models.ForeignKey('points.Point', on_delete=models.CASCADE, related_name='+')
    panels = [
        FieldPanel('point'),
    ]


class GeoPage(Page):
    content = StreamField([
        ('header', HeaderBlock(label="Заглавный блок")),
        ('slider', SliderBlock()),
    ], blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('content'),
        InlinePanel('page_points', label="Points"),
    ]

    def __str__(self):
        return self.title