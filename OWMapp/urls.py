# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 19:38:58 2017

@author: Allison Kaufman


OWMapp urls
"""

from django.conf.urls import url, include 
from django.contrib.auth import views as auth_views
from django.contrib import admin


from OWMapp import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/OWMapp'}, name='logout'),
    url(r'^weather/$', views.weather, name='weather'),
    url(r'^activities/$', views.activities, name='activities'),
    url(r'^oauth/', include('social_django.urls', namespace='social')), 
    url(r'^admin/', admin.site.urls),
]

