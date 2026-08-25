from django.shortcuts import render
from django.utils import timezone

def upload_data(request):
    context = {}
    return render(request, 'upload_data/upload_data.html', context)
