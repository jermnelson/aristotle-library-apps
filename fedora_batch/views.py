"""
 mod:`views` Fedora Batch App Views
"""
from app_settings import APP,fedora_repo
from app_helpers import repository_move,repository_update
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
    

def object_mover(request):
    """
    Displays and process form for moving objects by their PID to
    a different parent PID

    :param request: Django request
    """
    if request.method == 'POST':
        mover_form = MoverForm(request.POST)
        if mover_form.is_valid():
            collection_pid = mover_form.cleaned_data['collection_pid']
            source_pid = mover_form.cleaned_data['source_pid']
            repository_move(source_pid,collection_pid)
            new_log = RepositoryMovementLog(collection_pid=collection_pid,
                                            source_pid=source_pid)
            new_log.save()
            message = 'PID %s moved to collection PID %s' % (source_pid,
                                                             collection_pid)
            return direct_to_template(request,
                                      'repository/index.html',
                                      {'history': RepositoryMovementLog.objects.all(),
                                       'message':message})
