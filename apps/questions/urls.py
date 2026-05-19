from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.question_create, name='question_create'),
    path('category/create/', views.category_create, name='category_create'),
]
