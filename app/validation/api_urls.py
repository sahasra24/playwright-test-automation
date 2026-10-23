from django.urls import path

from . import api

urlpatterns = [
    path("health/", api.health, name="api-health"),
    path("validate/", api.validate, name="api-validate"),
    path("runs/", api.run_list, name="api-run-list"),
    path("runs/<int:pk>/", api.run_detail, name="api-run-detail"),
]
