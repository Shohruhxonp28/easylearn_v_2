from django.urls import path
from . import views

urlpatterns = [
    path('', views.arena_list, name='arena_list'),
    path('<int:arena_id>/', views.arena_detail, name='arena_detail'),
    path('<int:arena_id>/join/', views.arena_join, name='arena_join'),
    path('<int:arena_id>/live/', views.arena_live, name='arena_live'),
    path('<int:arena_id>/battle/', views.arena_start_battle, name='arena_start_battle'),
    path('<int:arena_id>/leaderboard/', views.arena_leaderboard, name='arena_leaderboard'),
]
