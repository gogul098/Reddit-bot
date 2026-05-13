from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_view, name='analyze'),
    path('status/<str:task_id>/', views.status_view, name='status'),
]
