"""
 :mod:`forms` MARCR App forms module
"""
__author__ = 'Jeremy Nelson'

from django import forms

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



class SearchForm(forms.Form):
    query = forms.CharField(max_length=255)
    query_type = forms.ChoiceField(choices=SEARCH_CHOICES)
    

