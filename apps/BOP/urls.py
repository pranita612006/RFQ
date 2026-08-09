from django.urls import path
from . import views

urlpatterns = [
    path("BOP/", views.BOP_form, name="BOP"),
    path("BOP/get_bop_details/", views.get_bop_details, name="get_bop_details"),
    path("BOP/get_bop_autofill_data/", views.get_bop_autofill_data, name="get_bop_autofill_data"),
    path("BOP/save/", views.save_bop_form, name="save_bop_form"),
    path("BOP/delete/", views.delete_bop_form, name="delete_bop_form"),
    path("BOP/get_bop_tooling_options/", views.get_bop_tooling_options, name="get_bop_tooling_options"),
    path("BOP/get_bop_tab_descriptions/", views.get_bop_tab_descriptions, name="get_bop_tab_descriptions"),
    path("BOP/get_bop_tab_autofill_data/", views.get_bop_tab_autofill_data, name="get_bop_tab_autofill_data"),
    path("BOP/resolve_bom_details/", views.resolve_bom_details, name="resolve_bom_details"),
    path("BOP/bom_details_modal/", views.get_bom_details_for_modal, name="bom_details_modal"),
    path("BOP/send_approval/", views.send_bop_approval, name="send_bop_approval"),
    path("BOP/ecn/", views.ecn_bop, name="ecn_bop"),

    # BOP Tab CRUD
    path("BOP/tab/save/", views.save_bop_tab, name="save_bop_tab"),
    path("BOP/tab/load/", views.load_bop_tab, name="load_bop_tab"),
    path("BOP/tab/delete/", views.delete_bop_tab, name="delete_bop_tab"),
    # BOP Tooling CRUD
    path("BOP/tolling/save/", views.save_bop_tolling, name="save_bop_tolling"),
    path("BOP/tolling/load/", views.load_bop_tolling, name="load_bop_tolling"),
    path("BOP/tolling/delete/", views.delete_bop_tolling, name="delete_bop_tolling"),
    # Cell Alignment CRUD
    path("BOP/cell_alignment/save/", views.save_cell_alignment, name="save_cell_alignment"),
    path("BOP/cell_alignment/load/", views.load_cell_alignment, name="load_cell_alignment"),
    path("BOP/cell_alignment/delete/", views.delete_cell_alignment, name="delete_cell_alignment"),
    # Copy BOP Table (Access VBA btn_CreateTable_Click equivalent)
    path("BOP/copy_table/", views.copy_bop_table, name="copy_bop_table"),
    path("BOP/copy_bop_table/", views.copy_bop_table, name="copy_bop_table_alt"),

    # Download and Complete actions
    path("BOP/cell_alignment/download/", views.download_cell_alignment, name="download_cell_alignment"),
    path("BOP/cell_alignment/complete/", views.complete_cell_alignment, name="complete_cell_alignment"),
    path("BOP/tab/download/", views.download_bop_tab, name="download_bop_tab"),
    path("BOP/tab/complete/", views.complete_bop_tab, name="complete_bop_tab"),
    path("BOP/tolling/download/", views.download_bop_tolling, name="download_bop_tolling"),
    path("BOP/tolling/complete/", views.complete_bop_tolling, name="complete_bop_tolling"),

    # Copy and Paste BOP Table
    path("bop/copy/", views.copy_bop, name="copy_bop"),
    path("bop/paste/", views.paste_bop, name="paste_bop"),
]
