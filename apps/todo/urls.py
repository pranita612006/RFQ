from django.urls import path
from . import views

urlpatterns = [
    path("todo/", views.todo, name="todo"),
    path("todo/api/get_items_by_customer/", views.get_items_by_customer, name="todo_get_items_by_customer"),
    path("todo/api/get_project_type/", views.get_project_type, name="todo_get_project_type"),
    path("todo/api/export_todo/", views.export_todo, name="todo_export_todo"),
    path("todo/api/email_todo/", views.email_todo, name="todo_email_todo"),
]
