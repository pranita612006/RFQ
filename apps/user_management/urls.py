from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_management, name='user_management'),
    path('add/', views.add_user, name='add_user'),
    path('get/<str:username>/', views.get_user_details, name='get_user_details'),
    path('update/', views.update_user, name='update_user'),
    path('add-access/', views.add_user_access, name='add_user_access'),
    path('delete/', views.delete_user, name='delete_user'),
]
