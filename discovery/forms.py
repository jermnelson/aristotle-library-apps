"""
 :mod:`forms` MARCR App forms module
"""
__author__ = 'Jeremy Nelson'

from django import forms




class SearchForm(forms.Form):
    query = forms.CharField(max_length=255)

