from django.urls import path
from . import views

app_name = 'meet_app'

urlpatterns = [
    path('statistics/', views.statistics),
    path('waiting/<str:name>/', views.waiting),
    path('guest/<str:name>/<int:ts>/<str:sig>/', views.guest_waiting, name='guest_waiting'),
]