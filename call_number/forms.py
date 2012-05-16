"""
 :mod:`forms` Call Number Django App forms module
"""
__author__ = 'Jeremy Nelson'

from django import forms

class CallNumberAutoComplete(forms.form):
    query = forms.CharField(max_length=60,
                            label='Search by call-numbers')
