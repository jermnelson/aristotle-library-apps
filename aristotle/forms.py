"""
 forms.py - General forms used through-out the Aristotle Library App Project
"""
__author__ = 'Jeremy Nelson'

import logging,re
from django import forms

class FeedbackForm(forms.Form):
    """This form contains fields for a generic feedback form"""
    comment = forms.CharField(required=False,
                              label="Comment",
                              widget=forms.Textarea(attrs={'rows':3,
				                           'class':'span3',
                                                           'cols':30}))
    sender = forms.EmailField(required=False)
    subject = forms.CharField(max_length=100)
