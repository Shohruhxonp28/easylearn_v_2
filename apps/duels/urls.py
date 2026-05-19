from django.urls import path
from . import views

urlpatterns = [
    path('', views.duel_lobby, name='duel_lobby'),
    path('start/', views.start_duel, name='start_duel'),
]
