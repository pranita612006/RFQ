from django.urls import path
from . import views

urlpatterns = [
    path("ApproveRec/", views.ApproveRec_form, name="ApproveRec"),

    # Cascading dropdown APIs
    path("ApproveRec/api/customers/",   views.get_approve_customers, name="approverec_customers"),
    path("ApproveRec/api/items/",       views.get_approve_items,     name="approverec_items"),
    path("ApproveRec/api/bom_ids/",     views.get_approve_bom_ids,   name="approverec_bom_ids"),

    # BOM lines data
    path("ApproveRec/api/bom_lines/",   views.get_approve_bom_lines, name="approverec_bom_lines"),

    # Save action (global dropdown)
    path("ApproveRec/api/save_action/", views.save_approve_action,   name="approverec_save_action"),
    # Save action (per-row Edit button)
    path("ApproveRec/api/save_row_action/", views.save_approve_row_action, name="approverec_save_row_action"),

    # BOM New Part APIs
    path("ApproveRec/api/bom_new_parts/", views.get_approve_bom_new_parts, name="approverec_bom_new_parts"),
    path("ApproveRec/api/save_new_part_action/", views.save_approve_new_part_action, name="approverec_save_new_part_action"),

    # BOP APIs
    path("ApproveRec/api/bop_customers/",   views.get_approve_bop_customers, name="approverec_bop_customers"),
    path("ApproveRec/api/bop_items/",       views.get_approve_bop_items,     name="approverec_bop_items"),
    path("ApproveRec/api/bop_ids/",         views.get_approve_bop_ids,       name="approverec_bop_ids"),
    path("ApproveRec/api/bop_lines/",       views.get_approve_bop_lines,     name="approverec_bop_lines"),
    path("ApproveRec/api/save_bop_action/", views.save_approve_bop_action,   name="approverec_save_bop_action"),
    # Per-row Edit button endpoint for BOP
    path("ApproveRec/api/save_bop_row_action/", views.save_approve_bop_row_action, name="approverec_save_bop_row_action"),

    # RFQ APIs
    path("ApproveRec/api/rfq_updated_by/", views.get_rfq_updated_by, name="approverec_rfq_updated_by"),
    path("ApproveRec/api/rfq_records/",    views.get_rfq_records,    name="approverec_rfq_records"),
    path("ApproveRec/api/rfq_reopen/",     views.save_rfq_reopen,    name="approverec_rfq_reopen"),
]