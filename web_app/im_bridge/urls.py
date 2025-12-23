from django.urls import path
from . import views

urlpatterns = [
    path("register", views.register, name="im_register"),
    path("callback", views.callback, name="im_callback"),
]
