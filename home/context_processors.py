from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Profile, Sale, Stock


def ensure_profile(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        # Ensure the user has a profile to avoid template errors
        Profile.objects.get_or_create(user=user)
    return {}


def quick_stats(request):
    """Provide globally available quick stats for navbar/sidebar.

    Injects counts into both the request (for templates that access request.*)
    and the template context (for direct variable access).
    """
    try:
        today = timezone.now().date()
        product_count = Stock.objects.count()
        todays_products = Stock.objects.filter(date=today).count()
        todays_sales = Sale.objects.filter(date=today).count()
    except Exception:
        # In migrations or during startup, models may be unavailable
        product_count = 0
        todays_products = 0
        todays_sales = 0

    # Also attach to request for templates using request.*
    setattr(request, 'product_count', product_count)
    setattr(request, 'todays_products', todays_products)
    setattr(request, 'todays_sales', todays_sales)

    return {
        'product_count': product_count,
        'todays_products': todays_products,
        'todays_sales': todays_sales,
    }

