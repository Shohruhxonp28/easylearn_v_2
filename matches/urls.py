from django.urls import path
from . import views

urlpatterns = [
    path('duel/', views.duel_lobby, name='duel_lobby'),
    path('duel/start/', views.start_duel, name='start_duel'),
    path('duel/leave-queue/', views.leave_queue, name='leave_queue'),
    path('match/<int:match_id>/', views.match_play, name='match_play'),
    path('match/<int:match_id>/result/', views.match_result, name='match_result'),
]
