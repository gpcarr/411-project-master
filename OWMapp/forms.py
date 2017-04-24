# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 00:08:07 2017

@author: Allison Kaufman
"""

from django import forms
 
class WeatherForm(forms.Form):
    content = forms.CharField(max_length=256)