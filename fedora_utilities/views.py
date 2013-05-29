"""
 mod:`views` Fedora Batch App Views
"""
from app_settings import *
from app_helpers import *
from solr_helpers import SOLR_QUEUE, start_indexing
from aristotle.settings import INSTITUTION, FEDORA_URI, SOLR_URL
from aristotle.views import json_view
from aristotle.forms import FeedbackForm
from django.http import HttpResponse
from django.template import Context, loader
from django.shortcuts import redirect, render
from fedora_utilities.forms import *
from fedora_utilities.models import *
import os
import datetime


def default(request):
    """
    Default view for `Fedora Batch App`_

    :param request: HTTP Request
    """
    print("IN DEFAULT FOR FEDORA UTILTIES")
    add_obj_template_form = AddFedoraObjectFromTemplate()
    batch_ingest_form = BatchIngestForm()
    batch_modify_form = BatchModifyMetadataForm()
    object_mover_form = ObjectMovementForm()
    context = {'add_obj_form': add_obj_template_form,
               'app': APP,
               'feedback_form':FeedbackForm({'subject':'Fedora Utilities App'}),
               'feedback_context':request.get_full_path(),
               'ingest_form': batch_ingest_form,
               'institution': INSTITUTION,
               'message': request.session.get('msg'),
               'modify_form': batch_modify_form,
               'object_mover_form': object_mover_form,
               'solr_url': SOLR_URL}
    return render(request,
                  'fedora_utilities/app.html',
                  context)
    

def add_stub_from_template(request):
    """Handler for adding Fedora stub object using a template

    This function takes different Fedora Object Content Models and
    prefills a MODS XML stream for rapid ingestion of different
    stub records that are then modified later with contents.
    """
    if request.method == 'POST':
        add_obj_template_form = AddFedoraObjectFromTemplate(request.POST)
        if add_obj_template_form.is_valid():
            mods_context = {'year': add_obj_template_form.cleaned_data[
                'date_created']}
            digital_origin_id = add_obj_template_form.cleaned_data[
                'digital_origin']
            object_template = int(add_obj_template_form.cleaned_data[
                'object_template'])
            collection_pid = add_obj_template_form.cleaned_data[
                'collection_pid']
            number_stub_recs = add_obj_template_form.cleaned_data[
                'number_objects']
            content_model = 'adr:adrBasicObject'
            for row in DIGITAL_ORIGIN:
                if row[0] == int(digital_origin_id):
                    mods_context['digitalOrigin'] = row[1]
            if object_template == 1:
                mods_context['typeOfResource'] = 'text'
                mods_context['genre'] = 'newspaper'
            elif object_template == 2:
                mods_context['typeOfResource'] = 'sound recording'
                mods_context['genre'] = 'interview'
                content_model = 'adr:adrETD'
            elif object_template == 3:
                mods_context['typeOfResource'] = 'text'
                mods_context['genre'] = 'thesis'
            elif object_template == 4:
                mods_context['typeOfResource'] = 'moving image'
                mods_context['genre'] = 'videorecording'
            else:
                raise ValueError("Unknown Object Template={0}".format(
                    object_template))
            mods_xml_template = loader.get_template(
                'fedora_utilities/mods-stub.xml')
            mods_xml = mods_xml_template.render(Context(mods_context))
            create_stubs(mods_xml,
                         collection_pid,
                         number_stub_recs,
                         content_model)
            request.session['msg'] = \
                                   "Created {0} stub records in collection {1}".format(
                                       number_stub_recs,
                                       collection_pid)
            # return HttpResponse(mods_xml)
                                
    return redirect("/apps/fedora_utilities/")
                              

def batch_ingest(request):
    """
    Handler for batch ingest view in app
    """
    output = {}
    batch_ingest_form = BatchIngestForm(request.POST,request.FILES)
    if batch_ingest_form.is_valid():
        collection_pid = batch_ingest_form.cleaned_data['collection_pid']
        compressed_file = request.FILES['compressed_file']
        extension = os.path.splitext(compressed_file.name)[1]
        if ['.zip','.tar','.gz','.tgz'].count(extension) > 0:
            results = handle_uploaded_zip(compressed_file,collection_pid)
            request.session['msg'] = "Successfully ingested batch with the following PIDs:"
            for row in results:
                request.session['msg'] += "<p>{0}</p>".format(row)
            #! NEED TO LOG RESULTS
            output["msg"] = results
            return redirect("/apps/fedora_utilities/")
        else:
            raise ValueError("{0} is not a compressed file".format(compressed_file.name))
        output['collection_pid'] = collection_pid

@json_view
def index_solr(request):
    """
    Starts or updates view for indexing Fedora objects into Solr

    :param request:
    """
    output = {}
    if request.REQUEST.has_key('start'):
       start_indexing()
       output['msg'] = 'started indexing at {0}'.format(datetime.datetime.now().isoformat())
    else:
       output['msg'] = "{0} {1}".format(datetime.datetime.now().isoformat(),
                                        SOLR_QUEUE.get())
    return output

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
            return redirect("/apps/fedora_utilities/")
    else:
        mover_form = ObjectMovementForm()
    return render(request,
                  'fedora_utilities/app.html',
                  {'history': RepositoryMovementLog.objects.all(),
                   'message':message,
                   'ingest_form':ingest_form,
                   'institution':INSTITUTION,
                   'modify_form':modify_form,
                   'object_mover_form':ObjectMovementForm()})

