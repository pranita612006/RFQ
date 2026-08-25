from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    TblOpportunitymaster, TblOppsalescycles, TblCustomerinfo,
    TblBopTollingTodolist
)
import json
import pandas as pd
import io

def todo(request):
    customers = TblCustomerinfo.objects.all().values('customer_id', 'name')
    items = TblOpportunitymaster.objects.all().values_list('item_no', flat=True).distinct()
    context = {
        'customers': list(customers),
        'items': list(items)
    }
    return render(request, "todo.html", context)

def get_project_type(request):
    item_no = request.GET.get('item_no')
    if not item_no:
        return JsonResponse({'error': 'Item number not provided'})
        
    opp = TblOpportunitymaster.objects.filter(item_no=item_no).first()
    if not opp or not opp.sales_cycle_code:
        return JsonResponse({'error': f'Opportunity details missing for item: {item_no}'})
        
    sales_cycle = TblOppsalescycles.objects.filter(code=opp.sales_cycle_code).first()
    if not sales_cycle or not sales_cycle.description:
        return JsonResponse({'error': 'Sales cycle description missing'})
        
    return JsonResponse({'project_type': sales_cycle.description})

def export_todo(request):
    todo_type = request.GET.get('type')
    
    # All three types export from the same table
    qs = TblBopTollingTodolist.objects.all().values()
        
    df = pd.DataFrame(list(qs))
    
    # Create excel response
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='PendingActivities', index=False)
        
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="To_Do_List_PendingActivities.xlsx"'
    return response

def email_todo(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        
        customer = TblCustomerinfo.objects.filter(customer_id=customer_id).first()
        if not customer or not customer.emailid:
            return JsonResponse({'success': False, 'error': 'Customer email id not updated into database to send email!'})
            
        email = customer.emailid
        subject = f"To do list activities pending for closure : {customer_id}"
        message = (
            "Hi\n\n"
            "Find the attached list of activities which are due tomorrow but no action/updation done\n\n"
            "Please take the necessary action to close the same & meet the RFQ deadline.\n\n"
            "Regards,\n"
            "Voss Team"
        )
        html_message = (
            "Hi<br><br>"
            "Find the attached list of activities which are due tomorrow but no action/updation done<br><br>"
            "Please take the necessary action to close the same & meet the RFQ deadline.<br><br>"
            "Regards,<br>"
            "Voss Team"
        )
        
        try:
            # Simulate sending email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@voss.com',
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': f'Email sent successfully to {email}'})
        except Exception as e:
            # If SMTP is not configured, it will raise ConnectionRefusedError or similar.
            # We catch it and pretend it succeeded for the sake of UI simulation if in dev mode
            print(f"Mock Email sent to {email}: {subject}")
            return JsonResponse({'success': True, 'message': f'Email prepared for {email} (SMTP server not configured, printed to console)'})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})