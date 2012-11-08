"""
 :mod:`app_helpers` Fedora Batch App Helpers
"""
__author__ = "Jeremy Nelson"
from lxml import etree
import aristotle.settings as settings
from eulfedora.server import Repository
#import Queue,threading

MODS_NS = ''
repository = Repository(root=settings.FEDORA_ROOT,
                        username=settings.FEDORA_USER,
                        password=settings.FEDORA_PASSWORD)



def ingest_folder(file_path):
    # Queries repository and gets the next available pid in the coccc
    # namespace
    new_pid = repository.api.ingest(text=None)
    # Opens up the mods.xml from the directory
    mods = etree.XML(open(os.path.join(file_path,"mods.xml"),'rb').read())
    # Extracts title to set as Fedora Object's label
    title_element = mods.find("{{{0}}}titleInfo/{{{0}}}title".format(MODS_NS))
    repository.api.modifyObject(pid=new_pid,
                                label=title_element.text,
                                ownerId=FEDORA_USER,
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
    rels_ext = rels_ext_template.render(object_pid=new_pid,
                                        content_model="adr:adrBasicObject",
                                        parent_pid=COLLECTION_PID)
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
     
