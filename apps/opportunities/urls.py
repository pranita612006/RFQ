from django.urls import path
from . import views

urlpatterns = [
    path("opportunity/", views.opportunity_creation, name="opportunity_creation"),
    path('opportunity_creation/', views.opportunity_creation, name='opportunity_creation'),
    path('send-item-email/', views.send_item_email, name='send_item_email'),
    path('get_item_numbers/', views.get_item_numbers, name='get_item_numbers'),
    path('get_salespersons/', views.get_salespersons, name='get_salespersons'),
    path('get_sales_cycles/', views.get_sales_cycles, name='get_sales_cycles'),
    path('get_segments/', views.get_segments, name='get_segments'),
    path('get_opportunity_details/', views.get_opportunity_details, name='get_opportunity_details'),
      # Existing routes...
    path("opportunity/", views.opportunity_creation, name="opportunity_creation"),

    # New ECN Request route
    path("opportunity_ecn/", views.opportunitycreation_ecn, name="opportunitycreation_ecn"),
]
