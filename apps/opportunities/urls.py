from django.urls import path
from . import views

urlpatterns = [
    path("opportunity/", views.opportunity_creation, name="opportunity_creation"),
    path("opportunity_creation/", views.opportunity_creation),
    path("opportunity_ecn/", views.opportunitycreation_ecn, name="opportunitycreation_ecn"),

    path("send-item-email/", views.send_item_email, name="send_item_email"),

    # Lookup / data APIs
    path("get_item_numbers/", views.get_item_numbers, name="get_item_numbers"),
    path("get_salespersons/", views.get_salespersons, name="get_salespersons"),
    path("get_sales_cycles/", views.get_sales_cycles, name="get_sales_cycles"),
    path("get_segments/", views.get_segments, name="get_segments"),
    path("get_opportunity_details/", views.get_opportunity_details, name="get_opportunity_details"),
    path("get_item_info/", views.get_item_info, name="get_item_info"),
    path("get_ecn_details/", views.get_ecn_details, name="get_ecn_details"),
    path("check_rfq_lock/", views.check_rfq_lock, name="check_rfq_lock"),

    # CRUD
    path("opportunity/add/", views.add_opportunity, name="add_opportunity"),
    path("opportunity/update/", views.update_opportunity, name="update_opportunity"),
    path("opportunity/delete/", views.delete_opportunity, name="delete_opportunity"),
    path("opportunity/complete/", views.complete_opportunity, name="complete_opportunity"),

    # ECN CRUD
    path("opportunity_ecn/update/", views.update_ecn, name="update_ecn"),
    path("opportunity_ecn/delete/", views.delete_ecn, name="delete_ecn"),
]
