"""
 forms.py - Forms for uploading and downloading MARC records
"""
__author__ = 'Jeremy Nelson, Cindy Tappan'

import logging,re
from django import forms
from .models import ILSJobLog,JobLogNotes,RedisJobLog,SolrJobLog,marc_rec_types

class MARCRecordUploadForm(forms.Form):
    """This form contains fields that are necessary for MARC record loads"""
    raw_marc_record = forms.FileField(required=True,
                                      label="Single MARC File")
    record_type = forms.ChoiceField(required=True,
                                    label="Record Type",
                                    choices=marc_rec_types)
    notes = forms.CharField(required=False,
                            label="Notes",
                            widget=forms.Textarea(attrs={'rows':3,
                                                         'cols':30}))



class JobLogNotesForm(forms.ModelForm):
    """`JobLogNotesForm` is a Django form model for the `Notes` model
    """

    class Meta:
        fields = ('note_value',)
        model = JobLogNotes
        widgets = {
            'note_value':forms.Textarea(attrs={'cols':35,'rows':4}),
        }


class ILSJobLogForm(forms.ModelForm):
    """`ILSJobLogForm` is a django model form for adding a new
    ILSJobLog after running the job on the original MARC record
    uploaded file"""

    class Meta:
        model = ILSJobLog
        fields = ('new_records','overlaid_records','rejected_records')



class RedisJobLogForm(forms.ModelForm):
    """`RedisJobLogForm` is a django model form for adding a new
    log for after running the job on the original MARC record
    uploaded file"""

    class Meta:
        model = RedisJobLog

class SolrJobLogForm(forms.ModelForm):
    """`SolrJobLog` is a django model form for adding a new
    log for after running the job on the original MARC record
    uploaded file"""

    class Meta:
        model = SolrJobLog

##class UpdateRecordLoadLogForm(forms.ModelForm):
##    """`UpdateRecordLoadLogForm` is a Django model form for updating
##    an `RecordLoadLog`.
##    """
##
##    class Meta:
##        model = RecordLoadLog
##        fields = ('new_records',
##                  'overlaid_records',
##                  'rejected_records',
##                  'ils_result')
