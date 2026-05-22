from django.contrib.gis.db import models
from django.contrib.auth.models import User
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel
from django import forms
from django.contrib.gis.geos import Point as GEOSPoint


@register_snippet
class Point(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField(srid=4326)
    address = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_points')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.location.y}, {self.location.x})"

    class Meta:
        verbose_name = "Point"
        verbose_name_plural = "Points"

    panels = [
        FieldPanel('name'),
        FieldPanel('address'),
        FieldPanel('latitude'),
        FieldPanel('longitude'),
        FieldPanel('created_by'),
    ]



@register_snippet
class Message(models.Model):
    point = models.ForeignKey('Point', on_delete=models.CASCADE, related_name='authored_messages_points')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg by {self.author} at {self.point.name}"

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    panels = [
        FieldPanel('point'),
        FieldPanel('author'),
        FieldPanel('text'),
    ]

class PointForm(forms.ModelForm):
    latitude = forms.FloatField(
        min_value=-90, max_value=90,
        help_text="Широта (от -90 до 90)"
    )
    longitude = forms.FloatField(
        min_value=-180, max_value=180,
        help_text="Долгота (от -180 до 180)"
    )

    class Meta:
        model = Point
        fields = ['name', 'latitude', 'longitude', 'created_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.location:
            self.fields['latitude'].initial = self.instance.location.y
            self.fields['longitude'].initial = self.instance.location.x

    def save(self, commit=True):
        lat = self.cleaned_data['latitude']
        lon = self.cleaned_data['longitude']
        self.instance.location = GEOSPoint(lon, lat, srid=4326)
        return super().save(commit)


Point.base_form_class = PointForm


@register_snippet
class Artifact(models.Model):
    fastapi_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    synced_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "Артефакт"
        verbose_name_plural = "Артефакты"

    def __str__(self):
        return self.name

    panels = [
        FieldPanel("name", read_only=True),
        FieldPanel("description", read_only=True),
        FieldPanel("owner", read_only=True),
        FieldPanel("created_at", read_only=True),
        FieldPanel("synced_at", read_only=True),
    ]
