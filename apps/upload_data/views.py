from django.shortcuts import render
from apps.customer_creation.models import CustomerInfo

def upload_data(request):
    customers = CustomerInfo.objects.values_list('customer_id', flat=True).order_by('customer_id')
    context = {
        'customers': list(customers),
    }
    return render(request, 'upload_data/upload_data.html', context)
