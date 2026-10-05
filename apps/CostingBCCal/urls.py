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

    # BOC: tab-data autofill (LOCAL BOC + IMPORTED BOC)
    path("CostingBCCal/boc/tab-data/",             views.get_boc_tab_data,          name="get_boc_tab_data"),
    path("CostingBCCal/get-boc-tab-data/",         views.get_boc_tab_data,          name="get_boc_tab_data_alt"),
    path("CostingBCCal/boc/save-local-boc-data/",  views.save_local_boc_data,       name="save_local_boc_data"),
    path("CostingBCCal/save-local-boc-data/",      views.save_local_boc_data,       name="save_local_boc_data_alt"),

    # BOC: spec-compliant clean endpoint alias
    path("CostingBCCal/save-local-boc/",           views.save_local_boc_data,       name="save_local_boc"),
    path("CostingBCCal/boc/debug/",                views.boc_debug,                 name="boc_debug"),

    # BOC: Imported BOC tab-data fetch & save
    path("CostingBCCal/boc/imported-tab-data/",        views.get_imported_boc_tab_data,  name="get_imported_boc_tab_data"),
    path("CostingBCCal/get-imported-boc-tab-data/",    views.get_imported_boc_tab_data,  name="get_imported_boc_tab_data_alt"),
    path("CostingBCCal/boc/save-imported-boc-data/",   views.save_imported_boc_data,     name="save_imported_boc_data"),
    path("CostingBCCal/save-imported-boc-data/",       views.save_imported_boc_data,     name="save_imported_boc_data_alt"),
    path("CostingBCCal/save-imported-boc/",            views.save_imported_boc_data,     name="save_imported_boc"),

    # BOC: process (sync) and Excel download
    path("CostingBCCal/boc/process/",              views.process_boc_action,        name="process_boc_action"),
    path("CostingBCCal/boc/download/",             views.download_offer_sheet_excel, name="download_offer_sheet_excel"),
    path("CostingBCCal/api/get-items-by-customer/", views.get_items_by_customer,    name="get_items_by_customer"),

    # BOC: Descriptions for IMPORTED BOC Data Entry dropdown (auto-fill)
    path("CostingBCCal/boc/get-bop-descriptions/", views.get_bop_descriptions, name="get_bop_descriptions"),

    # BOC: Over View data fetching and record deletion
    path("CostingBCCal/boc/overview/data/", views.get_overview_boc_data, name="get_overview_boc_data"),
    path("CostingBCCal/boc/overview/delete/", views.delete_overview_boc_record, name="delete_overview_boc_record"),

    # RM + Conversion endpoints
    path("CostingBCCal/rm-conversion/process/",         views.process_rm_conversion,      name="process_rm_conversion"),
    path("CostingBCCal/rm-conversion/bom-data/",        views.get_rm_bom_tab_data,       name="get_rm_bom_tab_data"),
    path("CostingBCCal/rm-conversion/save-bom-data/",   views.save_rm_bom_data,          name="save_rm_bom_data"),
    path("CostingBCCal/rm-conversion/material-options/", views.get_rm_material_options,   name="get_rm_material_options"),
    path("CostingBCCal/rm-conversion/overview-data/",   views.get_rm_overview_data,      name="get_rm_overview_data"),
    path("CostingBCCal/rm-conversion/conversion-cost-data/", views.get_conversion_cost_data, name="get_conversion_cost_data"),
    path("CostingBCCal/rm-conversion/save-conversion-data/", views.save_conversion_cost_data, name="save_conversion_cost_data"),
    path("CostingBCCal/rm-conversion/add-entry/",       views.add_rm_conversion_entry,   name="add_rm_conversion_entry"),
    path("CostingBCCal/rm-conversion/delete-entry/",    views.delete_rm_conversion_entry, name="delete_rm_conversion_entry"),

    # Tooling Cost endpoints
    path("CostingBCCal/tooling-cost/data/",            views.get_tooling_cost_data,          name="get_tooling_cost_data"),
    path("CostingBCCal/tooling-cost/export/",          views.export_internal_tooling_cost,   name="export_internal_tooling_cost"),
    path("CostingBCCal/tooling-cost/recovery/data/",   views.get_recovery_tooling_cost_data, name="get_recovery_tooling_cost_data"),
    # Transport Cost endpoints
    path("CostingBCCal/transport-cost/data/", views.get_transport_cost_data, name="get_transport_cost_data"),
    path("CostingBCCal/transport-cost/save/", views.save_transport_cost_data, name="save_transport_cost_data"),

    # Download Offer Sheet endpoint
    path("CostingBCCal/download-offer-sheet/", views.download_offer_sheet, name="download_offer_sheet"),
    
    # Submit RFQ Completion endpoint
    path("CostingBCCal/submit-rfq-completion/", views.submit_rfq_completion, name="submit_rfq_completion"),
]

