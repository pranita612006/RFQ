from django.shortcuts import render
from django.utils import timezone

print(">>> LOADING apps.pages.views <<<")

def index(request):
    return render(request, 'pages/index.html')


# ✅ DASHBOARD VIEWS

def dashboard_v1(request):
    return render(request, 'pages/dashboard_v1.html')

def dashboard_v2(request):
    return render(request, 'pages/dashboard_v2.html')

def dashboard_v3(request):
    return render(request, 'pages/dashboard_v3.html')