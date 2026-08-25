from django.urls import path
from . import views

urlpatterns = [
    path("BOC/", views.BOC_form, name="BOC"),
    path("BOC/api/get_item_details/", views.get_item_details, name="boc_get_item_details"),
    path("BOC/api/get_boc_nos/", views.get_boc_nos, name="boc_get_boc_nos"),
    path("BOC/api/get_boc_details/", views.get_boc_details, name="boc_get_boc_details"),
    path("BOC/api/create_boc/", views.create_boc, name="boc_create"),
    path("BOC/api/save_boc/", views.save_boc, name="boc_save"),
    path("BOC/api/delete_boc/", views.delete_boc, name="boc_delete"),
    path("BOC/api/ecn_boc/", views.ecn_boc, name="boc_ecn"),
    path("BOC/api/send_approval_boc/", views.send_approval_boc, name="boc_send_approval"),
    path("BOC/api/add_boc_tooling/", views.add_boc_tooling, name="boc_add_tooling"),
    path("BOC/api/save_boc_tooling/", views.save_boc_tooling, name="boc_save_tooling"),
    path("BOC/api/delete_boc_tooling/", views.delete_boc_tooling, name="boc_delete_tooling"),
    path("BOC/api/get_prod_tooling/", views.get_prod_tooling, name="boc_get_prod_tooling"),
    path("BOC/api/get_boc_status/", views.get_boc_status, name="boc_get_status"),
    path("BOC/api/save_boc_status/", views.save_boc_status, name="boc_save_status"),
    path("BOC/api/get_bom_cost/", views.get_bom_cost, name="boc_get_bom_cost"),
    path("BOC/api/save_bom_cost/", views.save_bom_cost, name="boc_save_bom_cost"),
    path("BOC/api/get_bom_settle/", views.get_bom_settle, name="boc_get_bom_settle"),
    path("BOC/api/save_bom_settle/", views.save_bom_settle, name="boc_save_bom_settle"),
]