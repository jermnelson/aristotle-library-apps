"""
 mod:`views` Fedora Batch App Views
"""
from .app_settings import *
from .app_helpers import *

##from solr_helpers import SOLR_QUEUE, start_indexing
from aristotle.settings import INSTITUTION, FEDORA_URI, FEDORA_MODEL, SOLR_URL
from aristotle.views import json_view
from aristotle.forms import FeedbackForm
from django.contrib.auth.decorators import login_required
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
    batch_ingest_form = BatchIngestForm()
    batch_modify_form = BatchModifyMetadataForm()
    object_mover_form = ObjectMovementForm()

    context = {'app': APP,
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

def __process_form_list__(name, request, context):
    "Helper function takes a name and updates context"
    if request.POST.has_key(name):
        listing = request.POST.getlist(name)
        if listing is not None and len(listing) > 0:
            for row in listing:
                if len(row) > 0:
                    if context.has_key(name):
                        context[name].append(row)
                    else:
                        context[name] = [row,]

def __process_form_free_text__(name, request, context):
    """Helper function takes a name and checks for free form value,
    if free_form is present takes precedent over select options"""
    selected_option = request.POST.get(name, '')
    free_text = request.POST.get('{0}_free_form'.format(name), '')
    if len(free_text) > 0:
        context[name] = free_text
    elif selected_option is not None and len(selected_option) > 0:
        context[name] = selected_option

def add_stub_from_template(request):
    """Handler for adding Fedora stub object using a template

    This function takes different Fedora Object Content Models and
    prefills a MODS XML stream for rapid ingestion of different
    stub records that are then modified later with contents.
    """
    if request.method == 'POST':
        add_obj_template_form = AddFedoraObjectFromTemplate(request.POST)
        if add_obj_template_form.is_valid():
            mods_context = {'dateCreated': add_obj_template_form.cleaned_data[
                'date_created'],
                            'contributors': [],
                            'corporate_contributors': [],
                            'creators': [],
                            'corporate_creators': [],
                            'organizations': [],
                            'schema_type': 'CreativeWork', # Default,
                            'subject_people': [],
                            'subject_places': [],
                            'subject_topics': [],
                            'title': add_obj_template_form.cleaned_data['title']
                            }

            __process_form_list__('creators', request, mods_context)
            __process_form_list__('corporate_creators', request, mods_context)
            __process_form_list__('contributors', request, mods_context)
            __process_form_list__('corporate_contributors',
                                  request,
                                  mods_context)

            __process_form_list__('subject_people', request, mods_context)
            __process_form_list__('subject_places', request, mods_context)
            __process_form_list__('organizations', request, mods_context)
            __process_form_list__('subject_topics', request, mods_context)
            __process_form_list__('genre', request, mods_context)
            __process_form_free_text__('genre', request, mods_context)
            admin_note = add_obj_template_form.cleaned_data[
                'admin_note']
            if len(admin_note) > 0:
                mods_context['admin_note'] = admin_note
            description = add_obj_template_form.cleaned_data[
                'description']
            if len(description) > 0:
                mods_context['description'] = description
            alt_title = add_obj_template_form.cleaned_data[
                'alt_title']
            if len(alt_title) > 0:
                mods_context['alt_title'] = alt_title
            rights_holder = add_obj_template_form.cleaned_data[
                'rights_holder']
            if len(rights_holder) > 0:
                mods_context['rights_statement'] = rights_holder

            digital_origin_id = add_obj_template_form.cleaned_data[
                'digital_origin']
            object_template = int(add_obj_template_form.cleaned_data[
                'object_template'])
            collection_pid = add_obj_template_form.cleaned_data[
                'collection_pid']
            number_stub_recs = add_obj_template_form.cleaned_data[
                'number_objects']
            mods_context['form'] = add_obj_template_form.cleaned_data['form']
            mods_context['typeOfResource'] = add_obj_template_form.cleaned_data[
                'type_of_resource']
            for row in DIGITAL_ORIGIN:
                if row[0] == int(digital_origin_id):
                    mods_context['digitalOrigin'] = row[1]
            mods_context['language'] = 'English'
            mods_context['publication_place'] = PUBLICATION_PLACE
            mods_context['publisher'] = PUBLISHER
            extent = add_obj_template_form.cleaned_data['extent']
            if len(extent) > 0:
                mods_context['extent'] = extent
            if object_template == 1:
                mods_context['alt_title'] = add_obj_template_form.cleaned_data[
                    'alt_title']

                mods_context['subject_topics'].extend(['Meeting minutes',
                                               'Universities and colleges'])
                mods_context['subject_topics'] = list(set(mods_context['subject_topics']))
                mods_context['subject_places'] = list(set(
                    mods_context['subject_places']))



            elif object_template == 2:
                __process_form_free_text__('frequency',
                                           request,
                                           mods_context)
                mods_context['typeOfResource'] = 'text'
                mods_context['corporate_contributors'] = []
                mods_context['publisher'] = PUBLISHER
                mods_context['subject_topics'] = list(set(mods_context['subject_topics']))
            elif object_template == 3:
                mods_context['schema_type'] = 'AudioObject'
            elif object_template == 4:
                mods_context['schema_type'] = 'VideoObject'
            elif object_template == 5:
                pass
            else:
                raise ValueError("Unknown Object Template={0}".format(
                    object_template))
            mods_xml_template = loader.get_template(
                'fedora_utilities/mods-stub.xml')
            mods_xml = mods_xml_template.render(Context(mods_context))
            create_stubs(mods_xml,
                         mods_context['title'],
                         collection_pid,
                         number_stub_recs,
                         FEDORA_MODEL)
            request.session['msg'] = \
                                   "Created {0} stub records in collection {1}".format(
                                       number_stub_recs,
                                       collection_pid)
            return redirect("/apps/fedora_utilities/add_stub")
    else:
        add_obj_template_form = AddFedoraObjectFromTemplate()
        context = {'active': 'add_stub',
                   'add_obj_form': add_obj_template_form,
                   'app': APP,
                   'feedback_form':FeedbackForm({'subject':'Fedora Utilities App'}),
                   'feedback_context':request.get_full_path(),
                   'institution': INSTITUTION,
                   'message': request.session.get('msg')}
        return render(request,
                      'fedora_utilities/add-object-from-template.html',
                      context)



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
##       start_indexing()
       output['msg'] = 'started indexing at {0}'.format(datetime.datetime.now().isoformat())
    else:
        pass
##       output['msg'] = "{0} {1}".format(datetime.datetime.now().isoformat(),
##                                        SOLR_QUEUE.get())
    return output

def object_mover(request):
    """
    Displays and process form for moving objects by their PID to
    a different parent PID

    :param request: Django request
    """
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
                  'fedora_utilities/pid-mover.html',
                  {'app': APP,
                   'history': ObjectMovementLog.objects.all(),
                   'message':message,
                   'institution':INSTITUTION,
                   'object_mover_form':ObjectMovementForm()})

