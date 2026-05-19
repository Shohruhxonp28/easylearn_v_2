from django.urls import path
from . import views

urlpatterns = [
    path('<int:match_id>/play/', views.match_play, name='match_play'),
    path('<int:match_id>/submit/', views.submit_answer_view, name='submit_answer'),
    path('<int:match_id>/result/', views.match_result, name='match_result'),
]
