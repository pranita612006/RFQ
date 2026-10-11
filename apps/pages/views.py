from django.shortcuts import render, redirect
from django.db import connection
from .dashboard_service import (
    get_dashboard_v1_data,
    get_dashboard_v2_data,
    get_dashboard_v3_data
)

print(">>> LOADING apps.pages.views with real dynamic data <<<")

def index(request):
    return dashboard_v1(request)


# ✅ REAL DYNAMIC DASHBOARD VIEWS

def dashboard_v1(request):
    """
    Dashboard v1 (Red Theme): Executive Business & RFQ Opportunity Pipeline Intelligence
    """
    active_customer_id = request.session.get('active_customer_id') or request.GET.get('customer_id')
    data = get_dashboard_v1_data(active_customer_id=active_customer_id)
    return render(request, 'pages/dashboard_v1.html', {'d': data})


def dashboard_v2(request):
    """
    Dashboard v2 (Purple Theme): Engineering, Costing & Manufacturing Progress
    """
    data = get_dashboard_v2_data()
    return render(request, 'pages/dashboard_v2.html', {'d': data})


def dashboard_v3(request):
    """
    Dashboard v3 (Light Blue Theme): Customer-Centric Account & Commercial Progress
    """
    selected_customer_id = request.GET.get('customer_id') or request.session.get('active_customer_id') or 'CUST-005'
    data = get_dashboard_v3_data(selected_customer_id=selected_customer_id)
    return render(request, 'pages/dashboard_v3.html', {'d': data})


def dashboard_search(request):
    """
    Real-time dynamic search bar handler:
    Searches across customers, opportunity items, and project names.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('dashboard_v1')

    # 1. Match customer ID or Customer Name
    try:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT customer_id FROM tbl_customerinfo 
                WHERE customer_id ILIKE %s OR name ILIKE %s
                ORDER BY customer_id ASC
                LIMIT 1
            """, [f'%{query}%', f'%{query}%'])
            row = cur.fetchone()
            if row:
                return redirect(f"/dashboard/v3/?customer_id={row[0]}")
    except Exception:
        pass

    # 2. Match Opportunity Item Number or Project Name
    try:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT customerid, item_no FROM tbl_opportunitymaster
                WHERE item_no ILIKE %s OR project_name ILIKE %s OR part_name ILIKE %s
                LIMIT 1
            """, [f'%{query}%', f'%{query}%', f'%{query}%'])
            row = cur.fetchone()
            if row and row[0]:
                return redirect(f"/dashboard/v3/?customer_id={row[0]}")
    except Exception:
        pass

    return redirect('dashboard_v1')