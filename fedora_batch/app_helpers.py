"""
 :mod:`app_helpers` Fedora Batch App Helpers
"""
__author__ = "Jeremy Nelson"
from lxml import etree
import aristotle.settings as settings
from eulfedora.server import Repository

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
     
