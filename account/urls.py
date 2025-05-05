from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
  path('register/', views.register, name='register'),
  path('login/', views.user_login, name='login'),
  path('profile/', views.profile, name='profile'),
  path('logout/', views.user_logout, name='logout'),
  path('deposit/', views.deposit, name='deposit'),
  path('spend/', views.spend, name='spend'),
  path('transactions/', views.transaction_history, name='transactions'),
  path('change-password/', views.change_password, name='change_password'),

]