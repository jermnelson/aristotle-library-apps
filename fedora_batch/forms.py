from django import forms
from fedora_batch.models import *

class BatchIngestForm(forms.Form):
    metadata_template = forms.FileField()
    target_directory = forms.CharField(max_length=255)
    
class BatchModifyMetadataForm(forms.ModelForm):

    class Meta:
        model = BatchModifyMetadataLog
        exclude = ('created_on')

class ObjectMovementForm(forms.ModelForm):

    class Meta:
        model = ObjectMovementLog
        
