"""
Django settings for xolo project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

# settings.py

from pathlib import Path
import os
from dotenv import load_dotenv  # Use python-dotenv to load environment variables

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
AUTH_USER_MODEL = 'account.User'


DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = ['https://localhost:8000']

# Application definition
INSTALLED_APPS = [
    'account',
    'core',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jazzmin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'xolo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'xolo.wsgi.application'

# Database configuration using Supabase
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Email settings for different email campaigns
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('DEFAULT_EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.getenv('DEFAULT_EMAIL_PORT', 587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('DEFAULT_EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('DEFAULT_EMAIL_PASSWORD')

# Additional email configurations for other email types
EMAIL_BACKENDS = {
    'AIRDROP': {
        'EMAIL_HOST': os.getenv('AIRDROP_EMAIL_HOST', 'smtp.gmail.com'),
        'EMAIL_PORT': os.getenv('AIRDROP_EMAIL_PORT', 465),
        'EMAIL_USE_TLS': os.getenv('AIRDROP_EMAIL_USE_TLS', 'True') == 'True',
        'EMAIL_HOST_USER': os.getenv('AIRDROP_EMAIL_USER'),
        'EMAIL_HOST_PASSWORD': os.getenv('AIRDROP_EMAIL_PASSWORD'),
    },
    'GIVEAWAY': {
        'EMAIL_HOST': os.getenv('GIVEAWAY_EMAIL_HOST', 'smtp.gmail.com'),
        'EMAIL_PORT': os.getenv('GIVEAWAY_EMAIL_PORT', 465),
        'EMAIL_USE_TLS': os.getenv('GIVEAWAY_EMAIL_USE_TLS', 'True') == 'True',
        'EMAIL_HOST_USER': os.getenv('GIVEAWAY_EMAIL_USER'),
        'EMAIL_HOST_PASSWORD': os.getenv('GIVEAWAY_EMAIL_PASSWORD'),
    },
    'REFUND': {
        'EMAIL_HOST': os.getenv('REFUND_EMAIL_HOST', 'smtp.gmail.com'),
        'EMAIL_PORT': os.getenv('REFUND_EMAIL_PORT', 465),
        'EMAIL_USE_TLS': os.getenv('REFUND_EMAIL_USE_TLS', 'True') == 'True',
        'EMAIL_HOST_USER': os.getenv('REFUND_EMAIL_USER'),
        'EMAIL_HOST_PASSWORD': os.getenv('REFUND_EMAIL_PASSWORD'),
    },
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

