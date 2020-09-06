"""udaanBoxOffice URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from booking.views import *
from django.conf.urls import url
from django.contrib.auth import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('screens', createScreen),
    url(r'^screens/(?P<screen_name>\w{0,50})/reserve', reserveTickets),
    url(r'^screens/(?P<screen_name>\w{0,50})/seats/', getAvailableSeats),
    url(r'^auth/', include('social_django.urls', namespace='social')),
    url('login/', loginView),
    url('home/', home, name='home')
]
