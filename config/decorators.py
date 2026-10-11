from functools import wraps

def require_active_customer(view_func):
    """
    Ensures views have safely initialized `request.active_customer` attributes
    without forcing an unwanted redirect to the customer selection page.
    This allows every page across the system to be opened directly.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Guarantee safe dictionary structure for request.active_customer
        if not hasattr(request, 'active_customer') or not isinstance(request.active_customer, dict):
            request.active_customer = {
                'id': '',
                'name': '',
                'search_name': '',
            }
        else:
            request.active_customer.setdefault('id', '')
            request.active_customer.setdefault('name', '')
            request.active_customer.setdefault('search_name', '')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

