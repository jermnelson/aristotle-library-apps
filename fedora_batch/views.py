"""
 mod:`views` Fedora Batch App Views
"""
from app_settings import APP,fedora_repo
from app_helpers import repository_move,repository_update
from aristotle.settings import INSTITUTION,FEDORA_URI
from django.views.generic.simple import direct_to_template
from django.shortcuts import redirect
from fedora_batch.forms import *
from fedora_batch.models import *

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
                               'message':request.session.get('msg'),
                               'modify_form':batch_modify_form,
                               'object_mover_form':object_mover_form})
    

def json_view(func):
    """
    Returns JSON results from method call, from Django snippets
    `http://djangosnippets.org/snippets/622/`_
    """
    def wrap(request, *a, **kw):
        response = None
        try:
            func_val = func(request, *a, **kw)
            assert isinstance(func_val, dict)
            response = dict(func_val)
            if 'result' not in response:
                response['result'] = 'ok'
        except KeyboardInterrupt:
            raise
        except Exception,e:
            exc_info = sys.exc_info()
            print(exc_info)
            logging.error(exc_info)
            if hasattr(e,'message'):
                msg = e.message
            else:
                msg = ugettext("Internal error: %s" % str(e))
            response = {'result': 'error',
                        'text': msg}
            
        json_output = json.dumps(response)
        return HttpResponse(json_output,
                            mimetype='application/json')
    return wrap

def object_mover(request):
    """
    Displays and process form for moving objects by their PID to
    a different parent PID

    :param request: Django request
    """
    ingest_form = BatchIngestForm()
    modify_form = BatchModifyMetadataForm()
    message = None
    if request.method == 'POST':
        mover_form = ObjectMovementForm(request.POST)
        if mover_form.is_valid():
            fedora_base_uri = '{0}fedora/repository/'.format(FEDORA_URI)
            collection_pid_raw = mover_form.cleaned_data['collection_pid']
            collection_pid = PersisentIdentifer.objects.get_or_create(fedora_url = '{0}'.format(collection_pid_raw),
                                                                      identifier=collection_pid_raw)[0]
            
                                                                      
            source_pid_raw = mover_form.cleaned_data['source_pid']
            source_pid = PersisentIdentifer.objects.get_or_create(fedora_url = '{0}'.format(source_pid_raw),
                                                                  identifier=source_pid_raw)[0]
            repository_move(source_pid.identifier,collection_pid.identifier)
            new_log = ObjectMovementLog(collection_pid=collection_pid,
                                        source_pid=source_pid)
            new_log.save()
            message = "{0} succesfully transfered to {1}".format(source_pid.identifier,
                                                                 collection_pid.identifier)
            request.session['msg'] = message
            return redirect("/apps/fedora_batch/")
    else:
        mover_form = ObjectMovementForm()
    return direct_to_template(request,
                              'fedora_batch/app.html',
                              {'history': RepositoryMovementLog.objects.all(),
                               'message':message,
                               'ingest_form':ingest_form,
                               'institution':INSTITUTION,
                               'modify_form':modify_form,
                               'object_mover_form':ObjectMovementForm()})
    
