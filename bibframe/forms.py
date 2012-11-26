"""
 :mod:`forms` MARCR App forms module
"""
__author__ = 'Jeremy Nelson'

from django import forms

search_options = [("all","All"),
                  ("work","Works"),
                  ("instance","Instances"),
                  ("authority-person","Person (authority)"),
                  ("authority-subject","Subject (authority)"),
                  ("annotation","Annotations")]

class MARC12toMARCRForm(forms.Form):
    marc_file_location = forms.CharField(max_length=255)
    
    
    

class MARCRSearchForm(forms.Form):
    search_options = forms.ChoiceField(choices=search_options)



    
    

