from django.contrib.gis.db import models
from django.contrib.auth.models import User


class Point(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField(srid=4326)  # srid=4326 указывает систему координат WGS 84
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.location.x}, {self.location.y})"


class Message(models.Model):
    point = models.ForeignKey(Point, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Msg by {self.author} at {self.point.name}"