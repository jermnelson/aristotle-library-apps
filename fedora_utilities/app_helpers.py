"""
 :mod:`app_helpers` Fedora Batch App Helpers
"""
__author__ = "Jeremy Nelson"
from lxml import etree
from django.template import Context,Template
import aristotle.settings as settings
from eulfedora.server import Repository
import os,mimetypes,shutil

MODS_NS = 'http://www.loc.gov/mods/v3'
repository = Repository(root=settings.FEDORA_ROOT,
                        username=settings.FEDORA_USER,
                        password=settings.FEDORA_PASSWORD)
RELS_EXT = open(os.path.join(settings.PROJECT_HOME,
                "fedora_utilities",
                "fixures",
                "rels-ext.xml"),"rb").read()



def handle_uploaded_zip(file_request,parent_pid):
    """
    Function takes a compressed file object from the Request
    (should be either a .zip, .tar, .gz, or .tgz), opens
    and extracts contents to a temp upload directory. Iterates
    through and attempts to ingest each folder into the 
    repository. Returns a list of status for each
    attempted ingestion.

    :param file_request: File from request 
    :param parent_pid: PID of parent collection
    :rtype: List of status from ingesting subfolders
    """
    statuses = []
    zip_filepath = os.path.join(settings.MEDIA_ROOT,file_request.name)
    zip_filename,zip_extension = os.path.splitext(file_request.name)
    zip_destination = open(zip_filepath,"wb")
    for chunk in file_request.chunks():
        zip_destination.write(chunk)
    zip_destination.close()
    if zip_extension == ".zip":
        import zipfile
        new_zip = zipfile.ZipFile(zip_filepath,'r')
    elif [".gz",".tar",".tgz"].count(zip_extension) > 0:
        import tarfile
        new_zip = tarfile.open(zip_filepath)
    else:
        raise ValueError("File {0} in handle_uploaded_zip not recognized".format(zip_filepath))
    zip_contents = os.path.join(settings.MEDIA_ROOT,zip_filename)
    new_zip.extractall(path=zip_contents)
    zip_walker = next(os.walk(zip_contents))[1]
    for folder in zip_walker:
        full_path = os.path.join(zip_contents,folder)
        if os.path.isdir(full_path) and not folder.startswith(".git"):
            statuses.append(ingest_folder(full_path,parent_pid))
        #shutil.rmtree(full_path)
    #os.remove(zip_contents)
    return statuses

def create_stubs(mods_xml,
                 parent_pid,
                 num_objects,
                 content_model='adr:adrBasicObject'):
    """Function creates 1-n number of basic Fedora Objects in a repository

    Parameters:
    mods_xml -- MODS XML used for all stub MODS datastreams
    parent_pid -- PID of Parent collection
    num_objects -- Number of stub records to create in the parent collection
    """
    for i in xrange(0, int(num_objects)):
        # Retrieves the next available PID
        new_pid = repository.api.ingest(text=None)
        # Sets Stub Record Title
        repository.api.modifyObject(pid=new_pid,
                                    label="{0} of {1} objects in {2}".format(
                                        i,
                                        len(num_objects),
                                        parent_pid),
                                    ownerId=settings.FEDORA_USER,
                                    state="A")
        # Adds MODS datastream to the new object
        repository.api.addDatastream(pid=new_pid,
                                     dsID="MODS",
                                     dsLabel="MODS",
                                     mimeType="application/rdf+xml",
                                     content=mods_xml)
        # Add RELS-EXT datastream
        rels_ext_template = Template(RELS_EXT)
        rels_ext_context = Context({'object_pid':new_pid,
                                    'content_model':content_model,
                                    'parent_pid':parent_pid})
        rels_ext = rels_ext_template.render(rels_ext_context)
        repository.api.addDatastream(pid=new_pid,
                                     dsID="RELS-EXT",
                                     dsLabel="RELS-EXT",
                                     mimeType="application/rdf+xml",
                                     content=rels_ext)
    return
        
        
    
    

def ingest_folder(file_path,
                  parent_pid,
                  content_model="adr:adrBasicObject"):
    # Queries repository and gets the next available pid
    new_pid = repository.api.ingest(text=None)
    # Opens up the mods.xml from the directory
    mods = etree.XML(open(os.path.join(file_path,"mods.xml"),'rb').read())
    # Extracts title to set as Fedora Object's label
    title_element = mods.find("{{{0}}}titleInfo/{{{0}}}title".format(MODS_NS))
    repository.api.modifyObject(pid=new_pid,
                                label=title_element.text,
                                ownerId=settings.FEDORA_USER,
                                state="A")
    # Adds MODS datastream to the new object
    repository.api.addDatastream(pid=new_pid,
                                 dsID="MODS",
                                 dsLabel="MODS",
                                 mimeType="application/rdf+xml",
                                 content=etree.tostring(mods))
    # create a file directory walker to find image files in the directory
    all_files = next(os.walk(file_path))[2]

    for filename in all_files:
        file_root,file_ext = os.path.splitext(filename)
        if file_ext != ".xml":
            content = open(os.path.join(file_path,filename),"rb").read()
            # Weird bug in Fedora doesn't recognize image/pjpeg for .jpg
            # files, manually sets mime_type to image/jpeg
            mime_type = mimetypes.guess_type(filename)[0]
            if file_ext == ".jpg":
                mime_type = "image/jpeg"
            result = repository.api.addDatastream(pid=new_pid,
                                                  controlGroup="M",
                                                  dsID=filename,
                                                  dsLabel=file_root,
                                                  mimeType=mime_type,
                                                  content=content) 
    # finally, add RELS-EXT datastream
    rels_ext_template = Template(RELS_EXT)
    rels_ext_context = Context({'object_pid':new_pid,
                                'content_model':content_model,
                                'parent_pid':parent_pid})
    rels_ext = rels_ext_template.render(rels_ext_context)
    repository.api.addDatastream(pid=new_pid,
                                 dsID="RELS-EXT",
                                 dsLabel="RELS-EXT",
                                 mimeType="application/rdf+xml",
                                 content=rels_ext)
    return new_pid

 

def repository_move(source_pid,collection_pid):
    """
    Helper view function takes a source_pid and collection_pid, 
    retrives source_pid RELS-EXT and updates 
    fedora:isMemberOfCollection value with new collection_pid

    :param source_pid: Source Fedora Object PID
    :param collection_pid: Collection Fedora Object PID
    """
    ns = {'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
          'fedora':'info:fedora/fedora-system:def/relations-external#'}

    repository = Repository(root=settings.FEDORA_ROOT,
                            username=settings.FEDORA_USER,
                            password=settings.FEDORA_PASSWORD)
    raw_rels_ext = repository.api.getDatastreamDissemination(pid=source_pid,
                                                             dsID='RELS-EXT')
    rels_ext = etree.XML(raw_rels_ext[0])
    collection_of = rels_ext.find('{%s}Description/{%s}isMemberOfCollection' %\
                                  (ns['rdf'],ns['fedora']))
    if collection_of is not None:
        collection_of.attrib['{%s}resource' % ns['rdf']] = "info:fedora/%s" % collection_pid
    repository.api.modifyDatastream(pid=source_pid,
                                    dsID="RELS-EXT",
                                    dsLabel="RELS-EXT",
                                    mimeType="application/rdf+xml",
                                    content=etree.tostring(rels_ext))

def repository_update(pid,mods_snippet):
    """
    Helper function takes a pid and a mods_snippet and either replaces the
    existing mods or adds the mods snippet to the MODS datastream.

    :param pid: PID of Fedora object
    :param mods_snippet: MODS snippet
    """
    pass
   
