from django.urls import path
from . import views

urlpatterns = [
    path("BlanketSales/", views.BlanketSales_form, name="BlanketSales"),
    path("BlanketSales/api/get_item_customer_details/", views.get_item_customer_details, name="get_item_customer_details"),
    path("BlanketSales/api/get_blanketso_details/", views.get_blanketso_details, name="get_blanketso_details"),
    path("BlanketSales/api/create_blanketso/", views.create_blanketso, name="create_blanketso"),
    path("BlanketSales/api/save_blanketso/", views.save_blanketso, name="save_blanketso"),
    path("BlanketSales/api/create_bso_table/", views.create_bso_table, name="create_bso_table"),
    path("BlanketSales/api/get_bso_lines/", views.get_bso_lines, name="get_bso_lines"),
    path("BlanketSales/api/add_bso_line/", views.add_bso_line, name="add_bso_line"),
    path("BlanketSales/api/save_bso_line/", views.save_bso_line, name="save_bso_line"),
    path("BlanketSales/api/delete_bso_line/", views.delete_bso_line, name="delete_bso_line"),
    path("BlanketSales/api/get_hsn_codes/", views.get_hsn_codes, name="get_hsn_codes"),
]