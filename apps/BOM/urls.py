# apps/BOM/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("BOM/", views.BOM_form, name="BOM"),  # name matches template
    path("BOM/ajax/action/", views.bom_ajax_action, name="bom_ajax_action"),
]
