from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def require_active_customer(view_func):
    """
    Decorator to ensure the user has selected a customer before accessing the view.
    Redirects to the customer selection page if session data is missing.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # We rely on the ActiveCustomerMiddleware having attached `request.has_active_customer`
        if not getattr(request, 'has_active_customer', False):
            messages.warning(request, "Please select a customer before proceeding.")
            return redirect('customer_creation') 
        return view_func(request, *args, **kwargs)
    return _wrapped_view
