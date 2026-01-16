from django.urls import path
from . import views

urlpatterns = [
    path('points/', views.PointCreateView.as_view(), name='point-create'),
    path('points/messages/', views.MessageCreateView.as_view(), name='message-create'),
    path('points/search/', views.search_points, name='point-search'),
    path('messages/search/', views.search_messages, name='message-search'),
]