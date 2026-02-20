from django.contrib.gis.db import models
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey


class GeoPagePoint(Orderable):
    page = ParentalKey('GeoPage', on_delete=models.CASCADE, related_name='page_points')
    point = models.ForeignKey('points.Point', on_delete=models.CASCADE, related_name='+')

    panels = [
        FieldPanel('point'),
    ]


class GeoPage(Page):
    intro = models.CharField(max_length=250, blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('body'),
        InlinePanel('page_points', label="Points"),
    ]

    def __str__(self):
        return self.title