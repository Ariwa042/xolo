from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, DepositForm, EmailAuthenticationForm
from .models import UserProfile, Deposit, Transactions, Payment_account, SubscriptionPlan, Subscription, Cryptocurrency
from django.db.models import Sum
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from core.models import Campaign
import logging
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings

logger = logging.getLogger(__name__)


# User registration view
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)

            login(request, user)
            


            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('account:profile')
        else:
            logger.debug(f'Form errors: {form.errors}')  # Log form errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'account/register.html', {'form': form})


# User login view
from django.contrib.auth.forms import AuthenticationForm
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('account:profile')  # Redirect to your dashboard or home page
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'account/login.html', {'form': form})



# User logout view
@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('account:login')


@login_required
def profile(request):
    user_profile = UserProfile.get_profile(request.user)
    
    # Get completed deposits
    deposits = Deposit.objects.filter(
        user=request.user,
        status='COMPLETED'
    )
    total_deposits = sum(
        deposit.subscription_plan.price 
        for deposit in deposits 
        if deposit.subscription_plan is not None
    )  # Re-enable total_deposits calculation

    # Get transactions
    transactions = Transactions.objects.filter(
        user=request.user
    ).select_related('subscription__plan')

    campaigns_count = Campaign.objects.filter(user=request.user).count()

    context = {
        'user_profile': user_profile,
        'total_deposits': total_deposits,
        'total_transactions': len(deposits),
        'transactions': transactions,
        'campaigns_count': campaigns_count,
    }
    return render(request, 'account/profile.html', context)


# Subscription plans view
@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    user_subscriptions = Subscription.objects.filter(
        user=request.user,
        is_active=True
    )
    return render(request, 'account/plans.html', {
        'plans': plans,
        'user_subscriptions': user_subscriptions
    })

# Subscribe to plan view
@login_required
def subscribe_to_plan(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    # Remove deposit creation from here
    return redirect('account:deposit')

# Deposit view
@login_required 
def deposit(request):
    payment_info = Payment_account.objects.first()
    crypto_info = Cryptocurrency.objects.all()

    # Ensure QR codes are generated for all cryptocurrencies
    for crypto in crypto_info:
        if not crypto.qr_code:
            crypto.save()

    if request.method == 'POST':
        form = DepositForm(request.POST, request.FILES)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.user = request.user
            deposit.payment_account = payment_info if deposit.payment_type == 'BANK' else None
            deposit.crypto_payment = form.cleaned_data.get('crypto_payment') if deposit.payment_type == 'CRYPTO' else None
            deposit.status = 'PENDING'
            
            deposit.save()
            
            # Send admin notification
            notify_admins_of_pending_payment(deposit)
            messages.success(request, 'Payment submitted and under review.')
            return redirect('account:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DepositForm()

    return render(request, 'account/deposit.html', {
        'form': form,
        'payment_info': payment_info,
        'crypto_info': crypto_info,
    })

# Subscription list view
#@login_required
#def subscription_list(request):
#    subscriptions = Subscription.objects.filter(user=request.user).order_by('-start_date')
#    return render(request, 'account/subscriptions.html', {
#        'subscriptions': subscriptions
#    })

# Transaction history view
@login_required
def transaction_history(request):
    # Get all deposits
    deposits = Deposit.objects.filter(
        user=request.user
    ).select_related('subscription_plan').order_by('-created_at')

    # Calculate total amount from completed deposits
    total_amount = sum(
    deposit.subscription_plan.price 
    for deposit in deposits 
    if deposit.status == 'COMPLETED' and deposit.subscription_plan is not None
    )

    return render(request, 'account/transactions.html', {
        'deposits': deposits,
        'total_amount': total_amount
    })

# Change password view
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keeps the user logged in
            messages.success(request, 'Your password was successfully updated!')
            logger.info(f'Password updated for user {user}')
            return redirect('account:profile')  # Redirect to profile page or another page after success
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'account/change_password.html', {'form': form})

def notify_admins_of_pending_payment(deposit):
    User = get_user_model()
    admins = User.objects.filter(is_superuser=True)
    
    subject = "New Subscription Payment Pending"
    message = f"""
    A new payment is pending approval:
    User: {deposit.user.username}
    Plan: {deposit.subscription_plan}
    Amount: {deposit.subscription_plan.currency}{deposit.amount}
    """
    
    admin_emails = [admin.email for admin in admins if admin.email]
    if admin_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True
        )
