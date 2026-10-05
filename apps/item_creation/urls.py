from django.urls import path
from . import views

urlpatterns = [
    # Main form (render + serves as the GET page)
    path("item_creation/", views.item_creation_form, name="item_creation"),

    # CRUD actions (POST via AJAX)
    path("item_creation/add/", views.add_item, name="item_creation_add"),
    path("item_creation/update/", views.update_item, name="item_creation_update"),
    path("item_creation/delete/", views.delete_item, name="item_creation_delete"),

    # Email
    path("item_creation/send-item-email/", views.send_item_email, name="item_creation_send_email"),

    # AJAX lookups
    path("get_template_data/", views.get_template_data, name="get_template_data"),
    path("get_item_details/", views.get_item_details, name="get_item_details"),
    path("get_hsn_gst/", views.get_hsn_gst, name="get_hsn_gst"),
    path("get_item_list/", views.get_item_list, name="get_item_list"),

    # ECN form
    path("ecn-request/", views.ecn_request_page, name="ecn_request_page"),
    path("ecn-request/details/", views.get_ecn_item_details, name="ecn_item_details"),
    path("ecn-request/create/", views.create_ecn, name="ecn_create"),
    path("ecn-request/delete/", views.delete_ecn, name="ecn_delete"),
]