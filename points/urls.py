from django.urls import path
from . import views

urlpatterns = [
    path('points/', views.PointCreateView.as_view(), name='point-create'),
    path('points/messages/', views.MessageCreateView.as_view(), name='message-create'),
    path('points/search/', views.search_points, name='point-search'),
    path('messages/search/', views.search_messages, name='message-search'),

    path('pages/', views.GeoPageListView.as_view(), name='page-list'),
    path('pages/<int:pk>/', views.GeoPageDetailView.as_view(), name='page-detail'),
]