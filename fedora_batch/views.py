"""
 mod:`views` Fedora Batch App Views
"""
from app_settings import APP,fedora_repo
from aristotle.settings import INSTITUTION
from django.views.generic.simple import direct_to_template
from fedora_batch.forms import *

def default(request):
    """
    Default view for `Fedora Batch App`_

    :param request: HTTP Request
    """
    batch_ingest_form = BatchIngestForm()
    batch_modify_form = BatchModifyMetadataForm()
    object_mover_form = ObjectMovementForm()
    return direct_to_template(request,
                              'fedora_batch/app.html',
                              {'app':APP,
                               'ingest_form':batch_ingest_form,
                               'institution':INSTITUTION,
                               'modify_form':batch_modify_form,
                               'object_mover_form':object_mover_form})
    
