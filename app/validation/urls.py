from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload, name="upload"),
    path("runs/<int:pk>/", views.run_detail, name="run-detail"),
]
