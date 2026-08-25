from django.shortcuts import render
from django.utils import timezone

def erp_data(request):
    current_date = timezone.localtime(timezone.now()).strftime("%d-%b-%y")
    context = {
        'current_date': current_date,
    }
    return render(request, 'erp_data/erp_data.html', context)
