import hashlib
from django import template

register = template.Library()


@register.filter
def gravatar_url(email, size=80):
    """
    Return a Gravatar URL for the given email address.
    Falls back to a generic avatar if no Gravatar is set.
    Usage:  {{ user.email|gravatar_url:80 }}
    """
    if not email:
        return f"https://ui-avatars.com/api/?name=Guest&size={size}&background=555&color=fff&rounded=true&bold=true"
    email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
    # d=404 so we can detect missing; use ui-avatars as fallback via the 404 default
    return (
        f"https://www.gravatar.com/avatar/{email_hash}"
        f"?s={size}&d=https%3A%2F%2Fui-avatars.com%2Fapi%2F"
        f"%3Fname%3D{email.strip().split('@')[0].replace('.', '+')}"
        f"%26size%3D{size}%26background%3D2563eb%26color%3Dfff%26rounded%3Dtrue%26bold%3Dtrue"
    )


@register.filter
def initials_avatar(name, size=80):
    """
    Return a ui-avatars URL for the user's name.
    Usage:  {{ user.get_full_name|initials_avatar:80 }}
    """
    safe_name = (name or "U").replace(" ", "+")
    return (
        f"https://ui-avatars.com/api/?name={safe_name}&size={size}"
        f"&background=2563eb&color=fff&rounded=true&bold=true"
    )
