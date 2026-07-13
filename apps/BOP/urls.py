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
    path("BOP/send_approval/", views.send_bop_approval, name="send_bop_approval"),
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
]
