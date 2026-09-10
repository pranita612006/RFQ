from django.urls import path
from . import views

urlpatterns = [
    # Main form page
    path("CostingBCCal/", views.CostingBCCal_form, name="CostingBCCal"),

    # Norms API endpoints
    path("CostingBCCal/norms/list/",        views.norms_list,        name="norms_list"),
    path("CostingBCCal/norms/dropdowns/",   views.norms_dropdowns,   name="norms_dropdowns"),
    path("CostingBCCal/norms/update/",      views.norms_update,      name="norms_update"),
    path("CostingBCCal/norms/change_path/", views.norms_change_path, name="norms_change_path"),
    path("CostingBCCal/norms/export/",      views.norms_export,      name="norms_export"),

    # Internal Conversion API & Export endpoints
    path("CostingBCCal/internal-conversion/data/",   views.internal_conversion_data,   name="internal_conversion_data"),
    path("CostingBCCal/internal-conversion/export/", views.internal_conversion_export, name="internal_conversion_export"),

    # Year Assignment Data HTMX endpoints
    path("CostingBCCal/assignment-year-data/",        views.load_assignment_year_data,   name="load_assignment_year_data"),
    path("CostingBCCal/assignment-year-data/update/", views.update_assignment_category,  name="update_assignment_category"),
    path("CostingBCCal/assignment-year-data/export/", views.export_dt_consolidate,       name="export_dt_consolidate"),

    # Cost autofill API — fetches cost from tbl_dtassigmentyeardata by item + year
    path("CostingBCCal/get-cost/", views.get_cost_by_item_category, name="get_cost_by_item_category"),

    path("CostingBCCal/dump-db/", views.dump_db, name="dump_db"),
]