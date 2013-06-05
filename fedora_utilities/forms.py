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

MARC_FREQUENCY = [('choose', 'Choose...'),
                  ('Semiweekly', 'Semiweekly - 2 times a week'),
                  ('Three times a week', 'Three times a week'),
                  ('Weekly', 'Weekly'),
                  ('Biweekly', 'Biweekly - every 2 weeks'),
                  ('Three times a month', 'Three times a month'),
                  ('Semimonthly', 'Semimonthly - 2 times a month'),
                  ('Monthly', 'Monthly'),
                  ('Bimonthly', 'Bimonthly - every 2 months'),
                  ('Quarterly', 'Quarterly'),
                  ('Three times a year', 'Three times a year'),
                  ('Semiannual', 'Semiannual - 2 times a year'),
                  ('Annual', 'Annual'),
                  ('Biennial', 'Biennial - every 2 years'),
                  ('Triennial', 'Triennial - every 3 years'),
                  ('Completely irregular', 'Completely irregular')]

OBJECT_TEMPLATES = [(0, 'Choose model'),
                    (1, 'Newsletter'),
                    (2, 'Podcast'),
                    (3, 'Thesis'),
                    (4, 'Video')]

class AddFedoraObjectFromTemplate(forms.Form):
    admin_note = forms.CharField(label='Administrative Notes',
                                 max_length=1500,
                                 required=False,
                                 widget=forms.Textarea(
                                      attrs={'rows':5}))
    collection_pid = forms.CharField(max_length=20,
                                     label="PID of Parent Collection")
    date_created = forms.CharField(label='Date Created')
    digital_origin = forms.ChoiceField(choices=DIGITAL_ORIGIN,
                                       label='Digital Origin',
                                       initial=1)
    description = forms.CharField(label='Description',
                                  max_length=1500,
                                  widget=forms.Textarea(
                                      attrs={'rows':5}),
                                  required=False)
    frequency = forms.ChoiceField(choices=MARC_FREQUENCY,
                                  label='Frequency',
                                  required=False)
    number_objects = forms.CharField(initial=1,
                                     label='Number of stub records',
                                     max_length=5)
    object_template = forms.ChoiceField(label='Content Model Template',
                                        choices=OBJECT_TEMPLATES,
                                        widget=forms.Select(
                                            attrs={'data-bind':'value: chosenContentModel, click: displayContentModel'}))
    organizations = forms.CharField(max_length=255,
                                    required=False)
    rights_holder = forms.CharField(max_length=120,
                                    label='Use and Reproduction Rights Holder',
                                    initial='Colorado College')
    title = forms.CharField(max_length=120,
                            label='Title')

                                        

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
