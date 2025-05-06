from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from account.models import Subscription

def subscription_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user has any active subscription
            subscription = Subscription.objects.filter(
                user=request.user,
                is_active=True,
                end_date__gt=timezone.now()
            ).first()
            
            if not subscription:
                messages.error(request, 'Active subscription required for this feature')
                return redirect('account:plans')
                
            # Check monthly usage
            monthly_usage = subscription.get_monthly_usage()
            if monthly_usage >= subscription.plan.max_emails_per_month:
                messages.error(request, f'Monthly limit of {subscription.plan.max_emails_per_month} emails reached')
                return redirect('core:campaign_list')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
