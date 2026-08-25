from django.urls import path
from . import views

urlpatterns = [
    path('', views.erp_data, name='erp_data'),
]
