from django.urls import path
from . import views

from django.conf import settings


app_name = 'account'
urlpatterns = [
	path('login', views.user_login, name='user_login'),
]
