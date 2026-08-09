# apps/BOM/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("BOM/", views.BOM_form, name="BOM"),
    
    # BOM Step 1 CRUD (matching BOP)
    path("BOM/save/", views.save_bom_form, name="save_bom_form"),
    path("BOM/delete/", views.delete_bom_form, name="delete_bom_form"),
    path("BOM/get_bom_details/", views.get_bom_details, name="get_bom_details"),
    path("BOM/send_approval/", views.send_bom_approval, name="send_bom_approval"),
    path("BOM/ecn/", views.ecn_bom, name="ecn_bom"),
    
    # Step 2 parts and autofill
    path("BOM/ajax/action/", views.bom_ajax_action, name="bom_ajax_action"),
    path("BOM/ajax/autofill/", views.bom_get_autofill_data, name="bom_get_autofill_data"),
    path("BOM/ajax/part_data/", views.bom_get_part_data, name="bom_get_part_data"),
    path("BOM/ajax/part_statuses/", views.bom_get_part_statuses, name="bom_get_part_statuses"),
    path("BOM/debug/ecn/", views.bom_ecn_columns, name="bom_ecn_columns"),  # TEMP
    
    # Production BOM endpoints
    path("BOM/validate_production_bom_part/", views.validate_production_bom_part, name="validate_production_bom_part"),
    path("BOM/save_bom_line_item/", views.save_bom_line_item, name="save_bom_line_item"),
    path("BOM/create_copy/", views.create_copy, name="create_copy"),

    # Part Details Master (New Part modal)
    path("BOM/ajax/part_master_dropdowns/", views.get_part_master_dropdowns, name="bom_part_master_dropdowns"),
    path("BOM/ajax/create_part_master/", views.create_part_master, name="bom_create_part_master"),
    
    # Copy BOM Trans
    path("BOM/copy_bom_trans/", views.copy_bom_trans, name="copy_bom_trans"),
    path("BOM/paste_bom_trans/", views.paste_bom_trans, name="paste_bom_trans"),
]
