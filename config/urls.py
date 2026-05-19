from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('questions/', include('apps.questions.urls')),
    path('duels/', include('apps.duels.urls')),
    path('arenas/', include('apps.arenas.urls')),
    path('matches/', include('apps.matches.urls')),
]
