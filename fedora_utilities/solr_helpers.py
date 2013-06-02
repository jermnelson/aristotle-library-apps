__author__= "Claire L Mattoon, Johnny Edward, Eric Ziecker"

import xml.etree.ElementTree as etree
import aristotle.settings as settings
import sunburnt
from app_helpers import repository
from multiprocessing import Process, Queue
print("AFTER IMPORT")

SOLR_QUEUE = Queue(maxsize=5)

MODS_NS = 'http://www.loc.gov/mods/v3'
solr_server = sunburnt.SolrInterface(settings.SOLR_URL)

FIELDNAMES = [
    'access', # Should have a constant value of "Online"
    'author', #namePart
    'bib_num', # Pid
    'contents', # Should be all of the text of a transcription (if present)
    'format', #! Incorrect this should not be a subject
    'full_title', #title
    'id', #system generated, should be the PID
    'location', #! Incorrect, this should be a constant of dacc
    'notes', #! Incorrect, only include public access notes (not record notes), abstract
    'personal_name', #namePart
    'summary', # abstract
    'title', # title
    'topic', #subject
    'url', # Should be the URL in the location
]

def get_title(mods):
    """
    Function takes the objects MODS and extracts and returns the text of the title.
    """
    title = mods.find("{{{0}}}titleInfo/{{{0}}}title".format(MODS_NS))
    if title is not None:
        return title.text

def get_topics(mods):
    """
    Function takes the objects MODS and returns the text of the topics.
    """
    output = []
    topics = mods.findall("{{{0}}}subject/{{{0}}}topic".format(MODS_NS))
    for topic in topics:
        output.append(topic.text)
    return output

def get_creators(mods):
    """
    Function takes the object's MODS and extracts and returns the text of the
    author or creator.

    :param mods: Etree XML of MODS datastream
    :rtype: List of creator names
    """
    output = []
    all_names = mods.findall("{{{0}}}name".format(MODS_NS))
    for name in all_names:
        roleTerm = name.find("{{{0}}}role/{{{0}}}roleTerm".format(MODS_NS))
        if roleTerm.text == 'creator':
            namePart = name.find("{{{0}}}namePart".format(MODS_NS))
            output.append(namePart.text)
    return output


def get_description(mods):
    """
    Extracts a description from various MODS elements

    :param mods: Etree XML of MODS datastream
    :rtype: A list of  description strings
    """
    output = []
    physical_desc = mods.find("{{{0}}}physicalDescription".format(MODS_NS))
    if physical_desc is not None:
        extent = physical_desc.find("{{{0}}}extent".format(MODS_NS))
        if extent is not None:
            output.append(extent.text)
        origin = physical_desc.find("{{{0}}}digitalOrigin".format(MODS_NS))
        if origin is not None:
            output.append(origin.text)
    return output


def get_format(mods):
    """
    Extracts format from the genre field

    :param mods: Etree XML of MODS datastream
    """
    genre = mods.find("{{{0}}}genre".format(MODS_NS))
    if genre is not None:
        return genre.text


def get_mods(pid):
    """
    Function attempts to extract the MODS datastream from the digital
    repository

    :param pid: PID of the object
    :rtype: Etree of the MODS datastream
    """
    # Save results of attempting to retrieve the MODS datstream from the
    # repository
    mods_result = repository.api.getDatastreamDissemination(pid=pid,
                                                            dsID="MODS")
    # Gets the raw XML from the result
    mods_xml = mods_result[0]
    # Returns the etree MODS xml object from the raw XML
    return etree.XML(mods_xml)

def get_notes(mods):
    """
    Function extracts all notes fields from MODS

    :param mods: Etree of the MODS datastream
    """
    notes = []
    all_notes = mods.find("{{{0}}}note".format(MODS_NS))
    if all_notes is None:
        return notes
    for note in all_notes:
        displayLabel = note.attribt.get('displayLabel')
        if displayLabel is not None:
            text = "{0} {1}".format(displayLabel, note.text)
        else:
            text = note.text
        notes.append(text)
    return notes

def get_publisher(mods):
    """
    Function extracts publisher from MODS

    :param mods: Etree of the MODS datastream
    """
    publisher = mods.find("{{{0}}}originInfo/{{0}}publisher".format(MODS_NS))
    if publisher is not None:
        return publisher.text

def get_published_year(mods):
    """
    Function extracts publisher from MODS

    :param mods: Etree of the MODS datastream
    """
    dateCreated = mods.find("{{{0}}}originInfo/{{0}}dateCreated".format(MODS_NS))
    if dateCreated is not None:
        return dateCreated.text



def get_summary(mods):
    """
    Function extracts abstract from MODS and returns text.
    """
    summary = mods.find("{{{0}}}abstract".format(MODS_NS))
    if summary is not None:
        return summary.text

def get_text(solr_doc,mods):
    """
    Function adds most of MODS record into general text field for
    searching

    :param solr_doc: Solr document dictionary
    :param mods: Etree of the MODS datastream
    """
    output = []
    for key,value in solr_doc.iteritems():
        if ['access','bib_num','id'].count(key) < 1:
            output.append(value)
    return output

def get_url(mods):
    """
    Function extracts URL location from MODS and returns text.
    """
    url = mods.find("{{{0}}}location/{{{0}}}url".format(MODS_NS))
    if url is not None:
        return url.text

def index_collection(collection_pid='coccc:top',recursive=True):
    """
    Method indexes all child elements in a Fedora Collection, if
    recursive is True, any collections in the children will call
    index_collection function for that child pid.A

    :param collection_pid: Collection of PID, default is top-level collection
                           object for the repository
    :param recursive: Boolean, if True will call the index_collection on any
                      subcollections in the collection
    """
    get_collection_sparql = '''PREFIX fedora: <info:fedora/fedora-system:def/relations-external#>
    SELECT ?a
    FROM <#ri>
    WHERE
    {
      ?a fedora:isMemberOfCollection <info:fedora/%s>
    }
    ''' % collection_pid
    csv_reader = repository.risearch.sparql_query(get_collection_sparql)
    for row in csv_reader:
        result = row.get('a')
        pid = result.split("/")[1]
        relationship = etree.XML(repository.api.getRelationship(pid)[0])
        index_digital_object(pid=pid)


def index_digital_object(**kwargs):
    pid = kwargs.get('pid')
    mods = get_mods(pid)
    if kwargs.has_key('format'):
        formatOf = kwargs.get('format')
    else:
        formatOf = get_format(mods)
        if formatOf is None:
            formatOf = 'Unknown'
        else:
            formatOf

    solr_doc = {'access':'Online',
                'bib_num':pid,
                'format':formatOf.title(),
                'location':'Digital Archives of Colorado College (DACC)',
                'id':pid}
    solr_doc['author'] = get_creators(mods)
    solr_doc['description'] = get_description(mods)
    solr_doc['title'] = get_title(mods)
    solr_doc['full_title'] = solr_doc['title']
    solr_doc['topic'] = get_topics(mods)
    solr_doc['summary'] = get_summary(mods)
    solr_doc['notes'] = get_notes(mods)
    solr_doc['personal_name'] = solr_doc['author']
    solr_doc['publisher'] = get_publisher(mods)
    solr_doc['pubyear'] = get_published_year(mods)
    solr_doc['text'] = get_text(solr_doc,mods)
    solr_doc['url'] = get_url(mods)
    print("Adding {0} with format {1} to Solr index".format(solr_doc['id'],
    solr_doc['format']))
    solr_server.add(solr_doc)
    solr_server.commit()

def index_manuscript(pid):
    """
    Function takes PID, extracts MODS, creates Solr document and attempts to ingest into Solr.
    """
    index_digital_object(pid=pid,format='Manuscript')

def index_process(dig_obj,queue):
    """
    Function adds result of indexing fedora digital object into
    Solr index.

    :param dig_obj: Digital Object
    """
    print("In index_process")
    index_digital_object(pid=dig_obj.pid)
    queue.put("Indexed {0} with PID={1} into Solr Index".format(dig_obj.label,dig_obj.pid))

def start_indexing(pid_prefix='coccc'):
    """
    Function starts Solr indexing queue for all objects in
    the repository.

    :param pid_prefix: PID prefix to search, defaults to CC
    """
    query = "{0}*".format(pid_prefix)
    print("Before get pid generator {0}".format(query))

    all_pids_generator = repository.find_objects(query = "{0}*".format(pid_prefix))
    print("after get pid generator {0}".format(all_pids_generator))
    while 1:
        try:
            print("Before extracting next digital object")
            digital_object = next(all_pids_generator)
            print("Digital object PID={0}".format(digital_object.pid))
            process = Process(target=index_process, args=(digital_object,SOLR_QUEUE))
            process.start()
            #process.join()
        except:
            break




