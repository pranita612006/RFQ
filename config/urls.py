from django.contrib import admin
from django.urls import include, path

from apps.pages import views as page_views
from apps.item_creation import views as item_views

urlpatterns = [
    # ECN REQUEST PAGE
    path(
        "ecn-request/",
        item_views.ecn_request_page,
        name="ecn_request_page",
    ),

    # DASHBOARD URLS
    path("dashboard/v1/", page_views.dashboard_v1, name="dashboard_v1"),
    path("dashboard/v2/", page_views.dashboard_v2, name="dashboard_v2"),
    path("dashboard/v3/", page_views.dashboard_v3, name="dashboard_v3"),

    # APP URLS
    path("", include("apps.opportunities.urls")),
    path("", include("apps.pages.urls")),
    path("", include("apps.dyn_dt.urls")),
    path("", include("apps.dyn_api.urls")),
    path("charts/", include("apps.charts.urls")),
    path("admin/", admin.site.urls),
    path("", include("admin_adminlte.urls")),
    path("", include("apps.todo.urls")),
    path("", include("apps.customer_creation.urls")),
    path("", include("apps.item_creation.urls")),
    path("", include("apps.feasibility_form.urls")),
    path("", include("apps.BOM.urls")),
    path("", include("apps.BOP.urls")),
    path("", include("apps.BOC.urls")),
    path("", include("apps.CostingBCCal.urls")),
    path("", include("apps.BlanketSales.urls")),
    path("", include("apps.ApproveRec.urls")),
    path("", include("apps.Report.urls")),
    path("user-management/", include("apps.user_management.urls")),
    path("upload-data/", include("apps.upload_data.urls")),
    path("erp-data/", include("apps.erp_data.urls")),
]
