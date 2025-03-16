from django.urls import path
from . import views

app_name = 'videocall'

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('create/', views.create_room, name='create_room'),
    path('room/<uuid:room_id>/', views.join_room, name='join_room'),
] 