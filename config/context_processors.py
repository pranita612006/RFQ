def active_customer(request):
    """
    Makes the currently selected customer available in all templates.
    Handles the fallback if no customer is selected (first-time visit).
    """
    # Check if the session exists, otherwise provide default None values
    return {
        'global_customer_id': request.session.get('active_customer_id', None),
        'global_customer_name': request.session.get('active_customer_name', ''),
        'global_customer_code': request.session.get('active_customer_search_name', ''), # Use search_name as code
        'has_active_customer': bool(request.session.get('active_customer_id')),
    }
