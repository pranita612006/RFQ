from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from functools import wraps

def require_active_customer(view_func):
    """
    Decorator to ensure the user has selected a customer before accessing the view.
    - For API / AJAX calls (Content-Type: application/json or X-Requested-With header):
      returns a JSON 403 error so fetch() doesn't receive an HTML page.
    - For normal page requests: redirects to the customer selection page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # We rely on the ActiveCustomerMiddleware having attached `request.has_active_customer`
        if not getattr(request, 'has_active_customer', False):
            # Detect API / AJAX requests
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or 'application/json' in request.headers.get('Content-Type', '')
                or 'application/json' in request.headers.get('Accept', '')
            )
            if is_ajax:
                return JsonResponse(
                    {'error': 'No active customer selected. Please select a customer first.'},
                    status=403
                )
            messages.warning(request, "Please select a customer before proceeding.")
            return redirect('customer_creation')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
