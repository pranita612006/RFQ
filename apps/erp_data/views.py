from django.shortcuts import render
from django.utils import timezone
from apps.customer_creation.models import CustomerInfo

def erp_data(request):
    current_date = timezone.localtime(timezone.now()).strftime("%d-%b-%y")
    customers = CustomerInfo.objects.values_list('customer_id', flat=True).order_by('customer_id')
    context = {
        'current_date': current_date,
        'customers': list(customers),
    }
    return render(request, 'erp_data/erp_data.html', context)
