__author__ = "Jeremy Nelson"
import datetime
from django import forms
from fedora_utilities.models import *
from eulfedora.server import Repository
from eulfedora.util import RequestFailed

repository = Repository()

DIGITAL_ORIGIN = [(1, 'born digital'),
                  (2, 'reformatted digital'),
                  (3, 'digitized microfilm'),
                  (4, 'digitized other analog')]

OBJECT_TEMPLATES = [(1, 'Newsletter'),
                    (2, 'Podcast'),
                    (3, 'Thesis'),
                    (4, 'Video')]

class AddFedoraObjectFromTemplate(forms.Form):
    collection_pid = forms.CharField(max_length=20,
                                     label="PID of Parent Collection")
    date_created = forms.CharField(max_length=5,
                                   label='Date Created',
                                   initial=datetime.datetime.utcnow().year)
    digital_origin = forms.ChoiceField(choices=DIGITAL_ORIGIN,
                                       label='Digital Origin',
                                       initial=1)
    number_objects = forms.CharField(initial=1,
                                     label='Number of stub records',
                                     max_length=5)
    object_template = forms.ChoiceField(choices=OBJECT_TEMPLATES,
                                        label='Content Model Template')
                                        

class BatchIngestForm(forms.Form):
    collection_pid = forms.CharField(max_length=20)
    compressed_file = forms.FileField(label="A .tar or .zip file",
                                      required=False)
##    target_directory = forms.FileField(label="Select Directory to upload",
##                                       required=False,
##                                       widget=forms.ClearableFileInput(attrs={"webkitdirectory":"",
##                                                                              "directory":"",
##                                                                              "mozdirectory":""}))
    
class BatchModifyMetadataForm(forms.ModelForm):

    class Meta:
        model = BatchModifyMetadataLog
        exclude = ('created_on')

class ObjectMovementForm(forms.Form):
    """
    `MoverForm` allows a user to input a Fedora Commons Repository PID and
    a new parent collection PID for moving the object.
    """
    collection_pid = forms.CharField(max_length=20,
                                     label="PID of target collection",
                                     help_text='PID of target collection')

    source_pid = forms.CharField(max_length=20,
                                 label="PID of source PID",
                                 help_text='PID of source Fedora Object')

    def clean_collection_pid(self):
        """
        Custom clean method for :class:`MoverForm.collection_pid` checks to see
        if PID exists in Repository, raise :mod:`forms.ValidationError` if PID
        not present.
        """
        data = self.cleaned_data['collection_pid']
        if data is not None:
            try:
                collection_object = repository.api.getObjectHistory(pid=data)
            except RequestFailed:
                raise forms.ValidationError("Collection PID %s not found in repository" % data)
        return data
