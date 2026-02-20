from django.contrib.gis.db import models
from django.contrib.auth.models import User
from wagtail.snippets.models import register_snippet


@register_snippet
class Point(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField(srid=4326)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_points')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.location.x}, {self.location.y})"
    
    class Meta:
        verbose_name = "Point"
        verbose_name_plural = "Points"


@register_snippet
class Message(models.Model):
    point = models.ForeignKey('Point', on_delete=models.CASCADE, related_name='authored_messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg by {self.author} at {self.point.name}"
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"