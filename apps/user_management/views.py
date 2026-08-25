from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db import connection
from django.utils import timezone
import logging
from .models import EmpDetails

logger = logging.getLogger(__name__)

def user_management(request):
    active_users = EmpDetails.objects.all().order_by('emp_username')
    
    # Dynamically pull designations from DB + default fallback list
    db_desigs = list(
        EmpDetails.objects
        .exclude(emp_designation__isnull=True)
        .exclude(emp_designation="")
        .values_list('emp_designation', flat=True)
        .distinct()
    )
    default_desigs = ["Developer", "Manager", "Engineer", "Designer", "Director", "Operator", "Administrator"]
    designations = sorted(list(set(db_desigs + default_desigs)))
    
    module_choices = [
        'Opportunity Creation', 'BOM Creation', 'BOP Creation',
        'BOC Creation', 'Costing', 'Sales Order', 'Report', 'Item Creation'
    ]
    
    context = {
        'active_users': active_users,
        'designations': designations,
        'module_choices': module_choices,
    }
    return render(request, 'user_management/user_management.html', context)


def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        fullname  = request.POST.get('fullname', '').strip()
        designation = request.POST.get('designation', '').strip()
        email     = request.POST.get('email', '').strip()
        is_admin  = request.POST.get('is_admin', 'No')
        user_type = request.POST.get('user_type', 'Standard User').strip()
        
        if not username:
            messages.error(request, "Username is required.")
            return redirect('user_management')
        
        if EmpDetails.objects.filter(emp_username=username).exists():
            messages.error(request, f"User '{username}' already exists.")
            return redirect('user_management')
        
        EmpDetails.objects.create(
            emp_username=username,
            emp_name=fullname,
            emp_designation=designation,
            email_id=email,
            is_admin=is_admin,
            user_type=user_type,
        )
        messages.success(request, f"User '{username}' added successfully.")
        return redirect('user_management')
    
    return redirect('user_management')


def get_user_details(request, username):
    user = get_object_or_404(EmpDetails, emp_username=username)
    
    # Use raw SQL since the table has no auto-id column
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT accessto, access_type, lastmodifieddate
               FROM tbl_empdetails_useraccess
               WHERE emp_username = %s
               ORDER BY accessto""",
            [username]
        )
        rows = cursor.fetchall()
    
    access_list = [
        {
            'access_to':      row[0],
            'access_type':    row[1],
            'last_modified':  row[2] or ''
        }
        for row in rows
    ]
    
    # Normalize is_admin value for the dropdown
    raw_admin = (user.is_admin or '').lower()
    is_admin_display = 'Yes' if raw_admin in ('true', 'yes', '1') else 'No'
    
    return JsonResponse({
        'username':     user.emp_username,
        'fullname':     user.emp_name or '',
        'designation':  user.emp_designation or '',
        'email':        user.email_id or '',
        'is_admin':     is_admin_display,
        'user_type':    user.user_type or '',
        'access_rights': access_list
    })


def update_user(request):
    if request.method == 'POST':
        username    = request.POST.get('username', '').strip()
        fullname    = request.POST.get('fullname', '').strip()
        designation = request.POST.get('designation', '').strip()
        email       = request.POST.get('email', '').strip()
        is_admin    = request.POST.get('is_admin', 'No')
        user_type   = request.POST.get('user_type', 'Standard User').strip()
        
        if not username:
            messages.error(request, "Username is required.")
            return redirect('user_management')
        
        updated = EmpDetails.objects.filter(emp_username=username).update(
            emp_name=fullname,
            emp_designation=designation,
            email_id=email,
            is_admin=is_admin,
            user_type=user_type,
        )
        
        if updated:
            messages.success(request, f"User '{username}' updated successfully.")
        else:
            messages.error(request, f"User '{username}' not found.")
        return redirect('user_management')
    
    return redirect('user_management')


def add_user_access(request):
    if request.method == 'POST':
        username    = request.POST.get('username', '').strip()
        access_to   = request.POST.get('access_to', '').strip()
        access_type = request.POST.get('access_type', '').strip()
        
        if not username:
            messages.error(request, "Please select a user first (use the 'Select User to Edit' dropdown).")
            return redirect('user_management')
        
        if not access_to or not access_type:
            messages.error(request, "Both Access To and Access Type are required.")
            return redirect('user_management')
        
        # Fetch user for user_type
        user = get_object_or_404(EmpDetails, emp_username=username)
        now_str = timezone.localtime(timezone.now()).strftime("%d-%m-%Y %I:%M:%S %p")
        
        # Raw SQL: upsert — update if exists, insert if not
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM tbl_empdetails_useraccess WHERE emp_username = %s AND accessto = %s",
                [username, access_to]
            )
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                cursor.execute(
                    """UPDATE tbl_empdetails_useraccess
                       SET access_type = %s, user_type = %s, lastmodifieddate = %s
                       WHERE emp_username = %s AND accessto = %s""",
                    [access_type, user.user_type, now_str, username, access_to]
                )
            else:
                cursor.execute(
                    """INSERT INTO tbl_empdetails_useraccess
                       (emp_username, accessto, access_type, user_type, lastmodifieddate)
                       VALUES (%s, %s, %s, %s, %s)""",
                    [username, access_to, access_type, user.user_type, now_str]
                )
        
        messages.success(request, f"Permission '{access_type}' on '{access_to}' saved for {username}.")
        return redirect('user_management')
    
    return redirect('user_management')


def delete_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        user = get_object_or_404(EmpDetails, emp_username=username)
        user.delete()
        messages.success(request, f"User '{username}' has been deleted.")
        return redirect('user_management')
    
    return redirect('user_management')
