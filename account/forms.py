from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Deposit, SubscriptionPlan

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, error_messages={
        'required': "Please enter your email address.",
        'invalid': "Enter a valid email address."
    })
    full_name = forms.CharField(max_length=100, error_messages={
        'required': "Please enter your full name.",
        'max_length': "Your full name must be at most 100 characters."
    })

    class Meta:
        model = User
        fields = ('full_name', 'email', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].error_messages = {
            'required': "Please enter a username.",
            'max_length': "Your username must be at most 150 characters.",
        }
        self.fields['password1'].error_messages = {
            'required': "Please enter a password.",
        }
        self.fields['password2'].error_messages = {
            'required': "Please confirm your password.",
            'password_mismatch': "The two password fields didn't match.",
        }


# Form for deposit
class DepositForm(forms.ModelForm):
    subscription_plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.all(),
        empty_label=None,
        label='Select Subscription Plan'
    )

    class Meta:
        model = Deposit
        fields = ['subscription_plan']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription_plan'].widget.attrs.update({
            'class': 'form-control',
            'onchange': 'updateAmount(this.value)'
        })


    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if not amount:
            raise forms.ValidationError("Amount is required.")
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

class EmailAuthenticationForm(AuthenticationForm):
    email = forms.EmailField(label='Email')

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        # Check if the email is associated with a user
        try:
            self.user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError('Invalid email or password.')

        # Authenticate using the email and password
        if not self.user.check_password(password):
            raise forms.ValidationError('Invalid email or password.')

        return self.cleaned_data