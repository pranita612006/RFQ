from django.urls import path
from . import views

urlpatterns = [
    path("item_creation/", views.item_creation_form, name="item_creation"),
    path("item_creation/send-item-email/", views.send_item_email, name="item_creation_send_email"),
    path("get_template_data/", views.get_template_data, name="get_template_data"),
    path("get_item_details/", views.get_item_details, name="get_item_details"),
    path("item_creation/", views.item_creation_page, name="item_creation_page"),
    path("ecn-request/", views.ecn_request_page, name="ecn_request_page"), 
]