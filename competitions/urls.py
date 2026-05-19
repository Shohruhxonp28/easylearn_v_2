from django.urls import path
from . import views

urlpatterns = [
    # Arena
    path('arena/', views.arena_list, name='arena_list'),
    path('arena/<int:arena_id>/', views.arena_detail, name='arena_detail'),
    path('arena/<int:arena_id>/match/<int:match_id>/', views.arena_match_play, name='arena_match_play'),
    path('arena/<int:arena_id>/match/<int:match_id>/result/', views.arena_match_result, name='arena_match_result'),
    path('arena/<int:arena_id>/leaderboard/', views.arena_leaderboard, name='arena_leaderboard'),

    # Tournament
    path('tournament/', views.tournament_list, name='tournament_list'),
    path('tournament/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('tournament/<int:tournament_id>/bracket/', views.tournament_bracket, name='tournament_bracket'),
    path('tournament/<int:tournament_id>/match/<int:tmatch_id>/', views.play_tournament_match, name='play_tournament_match'),
    path('tournament/<int:tournament_id>/match/<int:tmatch_id>/result/', views.tournament_match_result, name='tournament_match_result'),

    # Admin custom dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/create-question/', views.admin_create_question, name='admin_create_question'),
    path('admin-dashboard/create-tournament/', views.admin_create_tournament, name='admin_create_tournament'),
    path('admin-dashboard/start-tournament/<int:tournament_id>/', views.admin_start_tournament, name='admin_start_tournament'),
]
