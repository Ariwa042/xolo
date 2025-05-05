from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, DepositForm, SpendForm, EmailAuthenticationForm
from .models import UserProfile, Deposit, Spend, Transactions, Payment_account
from django.db.models import Sum
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from core.models import Campaign
import logging
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

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


# User profile view
@login_required
def profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    total_deposits = Deposit.objects.filter(user=request.user, status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0
    total_spent = Spend.objects.filter(user=request.user, status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0
    transactions = Transactions.objects.filter(user=request.user)
    campaigns_count = Campaign.objects.filter(user=request.user).count()

    context = {
        'user_profile': user_profile,
        'total_deposits': total_deposits,
        'total_spent': total_spent,
        'transactions': transactions,
        'campaigns_count': campaigns_count,
    }
    return render(request, 'account/profile.html', context)


# Deposit view

@login_required
def deposit(request):
    xp_packages = [
        {'amount': 1, 'cost': 1000},
        {'amount': 5, 'cost': 5000},
        {'amount': 10, 'cost': 10000},
        {'amount': 50, 'cost': 50000},
    ]

    payment_info = Payment_account.objects.first()  # Get the general payment info

    if request.method == 'POST':
        selected_amount = request.POST.get('amount')

        if selected_amount:
            form = DepositForm(request.POST)
            if form.is_valid():
                deposit = form.save(commit=False)
                deposit.user = request.user
                deposit.amount = selected_amount  # Set the selected amount
                deposit.status = 'PENDING'
                deposit.save()

                # Send email to all superusers or staff
                User = get_user_model()
                superusers_or_staff = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
                email_list = [user.email for user in superusers_or_staff if user.email]

                if email_list:
                    send_mail(
                        subject="New Deposit Pending Approval",
                        message=f"A user has made a deposit of {deposit.amount} XP. Please review and approve it.",
                        from_email= "Airstrike <cryptotracker.llc@gmail.com>",
                        recipient_list=email_list,
                        fail_silently=False,
                    )

                messages.success(request, 'Deposit created, pending approval.')
                return redirect('account:profile')
        else:
            messages.error(request, 'No amount was selected.')
            return redirect('account:deposit')
    else:
        form = DepositForm()

    context = {
        'form': form,
        'xp_packages': xp_packages,
        'payment_info': payment_info,
    }
    return render(request, 'account/deposit.html', context)



# Spend view
@login_required
def spend(request):
    if request.method == 'POST':
        form = SpendForm(request.POST)
        if form.is_valid():
            spend = form.save(commit=False)
            user_profile = UserProfile.objects.get(user=request.user)

            if user_profile.xp_balance >= float(spend.amount):
                spend.user = request.user
                spend.status = 'PENDING'
                spend.save()
                Transactions.objects.create(
                    user=request.user,
                    type='SPENT',
                    amount=spend.amount,
                    status='PENDING'
                )
                messages.success(request, 'Payment initiated, pending approval.')
            else:
                messages.error(request, 'Insufficient XP balance.')

            return redirect('account:profile')
    else:
        form = SpendForm()

    return render(request, 'account/spend.html', {'form': form})


# Transaction history view
@login_required
def transaction_history(request):
    deposits = Deposit.objects.filter(
        user=request.user).order_by('-created_at')
    spends = Spend.objects.filter(
       user=request.user).order_by('-created_at')
    return render(request, 'account/transactions.html', {
        'deposits': deposits,
        'spends': spends,
    })
#    context = {
#        'transactions': transactions
#    }
#    return render(request, 'account/transactions.html', context)

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
