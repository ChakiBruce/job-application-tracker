from django.urls import path

from . import views


app_name = "applications"
urlpatterns = [
    path("", views.application_list, name="list"),
    path("applications/new/", views.application_create, name="create"),
    path("applications/<int:pk>/status/", views.application_update_status, name="update_status"),
]
