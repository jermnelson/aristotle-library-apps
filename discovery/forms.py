"""
 :mod:`forms` MARCR App forms module
"""
__author__ = 'Jeremy Nelson'

from captcha.fields import CaptchaField
from django import forms

ANNOTATION_CHOICES = [("Description", "Describe"),
                      ("Review", "Review")]
                      

SEARCH_CHOICES = [("kw", "Keyword"),
                  ('au', u'Author'),
                  ('t', u'Title'),
                  ('jt', u'Journal Title'),
                  ('lc', u'LC Subject'),
                  ('med', u'Medical Subject'),
                  (None, u"Children's Subject"),
                  ('lccn', u'LC Call Number'),
                  ('gov', u'Gov Doc Number'),
                  ('is', u'ISSN/ISBN'),
                  ('dw', u'Dewey Call Number'),
                  ('medc', u'Medical Call Number'),
                  ('oclc', u'OCLC Number')]


class AnnotationForm(forms.Form):
    annotation_body = forms.CharField(
        widget=forms.Textarea(
            attrs={'data-bind': 'value: AnnotationBody'}))
    annotation_type = forms.ChoiceField(
        choices=ANNOTATION_CHOICES,
        widget=forms.Select(
            attrs={'data-bind': 'value: AnnotationType'}))
    captcha = CaptchaField()
    private = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={'data-bind': 'value: IsPrivateAnnotation'}))
    
                                                   


class SearchForm(forms.Form):
    query = forms.CharField(max_length=255,
                            widget=forms.TextInput(
                                attrs={'data-bind': 'value: QueryPhrase'}))
    query_type = forms.ChoiceField(choices=SEARCH_CHOICES,
                                   widget=forms.Select(
                                       attrs={'data-bind': 'value: QueryType'}))


    

