"""
 :mod:`marc21_facets` is a module for extracting facets for the MARCR datastore
 from MARC21 records. This code is derived from the Discovery Aristotle
 project's marc parser.
"""
__author__ = "Jeremy Nelson"
import re,logging
import marc21_maps,tutt_maps

LOCATION_RE = re.compile(r'\(\d+\)')
NONINT_RE = re.compile(r'\D')
PER_LOC_RE = re.compile(r'(tper*)')
REF_LOC_RE = re.compile(r'(tarf*)')


access_search = re.compile(r'ewww')
def get_access(record):
    '''Generates simple access field specific to CC's location codes

    :param record: MARC record
    :rtype: String message
    '''
    if record['994']:
        raw_location = record['994'].value()
        if access_search.search(raw_location):
            return 'Online'
        else:
            return 'In the Library'
    else:
        return 'In the Library'

def get_format(record):
    '''Generates format, extends existing Kochief function.

    :param record: MARC record
    :rtype: String of Format
    '''
    format = ''
    if record['007']:
        field007 = record['007'].value()
    else:
        field007 = ''
    leader = record.leader
    if len(leader) > 7:
        if len(field007) > 5:
            if field007[0] == 'a':
                if field007[1] == 'd':
                    format = 'Atlas'
                else:
                    format = 'Map'
            elif field007[0] == 'c':            # electronic resource
                if field007[1] == 'j':
                    format = 'Floppy Disk'
                elif field007[1] == 'r':        # remote resource
                    if field007[5] == 'a':    # has sound
                        format = 'Electronic'
                    else:
                        format = 'Electronic'
                elif field007[1] == 'o' or field007[1] == 'm':      # optical disc
                    format = 'CDROM'
            elif field007[0] == 'd':
                format = 'Globe'
            elif field007[0] == 'h':
                format = 'Microfilm'
            elif field007[0] == 'k': # nonprojected graphic
                if field007[1] == 'c':
                    format = 'Collage'
                elif field007[1] == 'd':
                    format = 'Drawing'
                elif field007[1] == 'e':
                    format = 'Painting'
                elif field007[1] == 'f' or field007[1] == 'j':
                    format = 'Print'
                elif field007[1] == 'g':
                    format = 'Photonegative'
                elif field007[1] == 'l':
                    format = 'Drawing'
                elif field007[1] == 'o':
                    format = 'Flash Card'
                elif field007[1] == 'n':
                    format = 'Chart'
                else:
                    format = 'Photo'
            elif field007[0] == 'm': # motion picture
                if field007[1] == 'f':
                    format = 'Videocassette'
                elif field007[1] == 'r':
                    format = 'Filmstrip'
                else:
                    format = 'Motion picture'
            elif field007[0] == 'o': # kit
                format = 'kit'
            elif field007[0] == 'q':
                format = 'musical score'
            elif field007[0] == 's':          # sound recording
                if leader[6] == 'i':             # nonmusical sound recording
                    if field007[1] == 's':   # sound cassette
                        format = 'Book On Cassette'
                    elif field007[1] == 'd':    # sound disc
                        if field007[6] == 'g' or field007[6] == 'z':
                            # 4 3/4 inch or Other size
                            format = 'Book On CD'
                elif leader[6] == 'j':        # musical sound recording
                    if field007[1] == 's':    # sound cassette
                        format = 'Cassette'
                    elif field007[1] == 'd':    # sound disc
                        if field007[6] == 'g' or field007[6] == 'z':
                            # 4 3/4 inch or Other size
                            format = 'Music CD'
                        elif field007[6] == 'e':   # 12 inch
                            format = 'LP Record'
            elif field007[0] == 'v':            # videorecording
                if field007[1] == 'f':
                    format = 'VHS Video'
                if field007[1] == 'd':        # videodisc
                    if field007[4] == 'v' or field007[4] == 'g':
                        format = 'DVD Video'
                    elif field007[4] == 's':
                        format = 'Blu-ray Video' 
                    elif field007[4] == 'b':
                        format = 'VHS Video' 
                    else:
                        #logging.error("247 UNKNOWN field007 %s for %s" % (field007[4],record.title()))
			pass
                elif field007[1] == 'f':        # videocassette
                    format = 'VHS Video'
                elif field007[1] == 'r':
                    format = 'Video Reel'
    # now do guesses that are NOT based upon physical description 
    # (physical description is going to be the most reliable indicator, 
    # when it exists...)
    if record['008']:
            field008 = record['008'].value()
    else:
            field008 = ''
    if leader[6] == 'a' and len(format) < 1:                # language material
        if leader[7] == 'a':
            format = 'Series' # Ask about?
        if leader[7] == 'c':
            format = 'Collection'
        if leader[7] == 'm':            # monograph
            if len(field008) > 22:
                if field008[23] == 'd':    # form of item = large print
                    format = 'Large Print Book'
                elif field008[23] == 's':    # electronic resource
                    format = 'Electronic'
                else:
                    format = 'Book'
            else:
                format = 'Book'
        elif leader[7] == 's':            # serial
            if len(field008) > 18:
                frequencies = ['b', 'c', 'd', 'e', 'f', 'i', 'j', 
                               'q', 's', 't', 'w']
                if field008[21] in frequencies:
                    format = 'Journal'
                elif field008[21] == 'm':
                    format = 'Book'
                else:
                    format = 'Journal'
            else:
                format = 'Journal'
    elif leader[6] == 'b' and len(format) < 1:
        format = 'Manuscript' 
    elif leader[6] == 'e' and len(format) < 1:
        format = 'Map'
    elif leader[6] == 'c' and len(format) < 1:
        format = 'Musical Score'
    elif leader[6] == 'g' and len(format) < 1:
        format = 'Video'
    elif leader[6] == 'd' and len(format) < 1:
        format = 'Manuscript noted music'
    elif leader[6] == 'j' and len(format) < 1:
        format = 'Music Sound Recordings'
    elif leader[6] == 'i' and len(format) < 1:
        if leader[7] != '#':
            format = 'Spoken Sound Recodings'
    elif leader[6] == 'k' and len(format) < 1:
        if len(field008) > 22:
            if field008[33] == 'i':
                format = 'Poster'
            elif field008[33] == 'o':
                format = 'Flash Cards'
            elif field008[33] == 'n':
                format = 'Charts'
    elif leader[6] == 'm' and len(format) < 1:
        format = 'Electronic'
    elif leader[6] == 'p' and len(format) < 1:
        if leader[7] == 'c':
            format = 'Collection'
        else:
            format = 'Mixed Materials'
    elif leader[6] == 'o' and len(format) < 1:
        if len(field008) > 22:
            if field008[33] == 'b':
                format = 'Kit'
    elif leader[6] == 'r' and len(format) < 1:
        if field008[33] == 'g':
            format = 'Games'
    elif leader[6] == 't' and len(format) < 1:
        if len(field008) > 22:
            if field008[24] == 'm':
                format = 'Thesis'
            elif field008[24] == 'b':
                format = 'Book'
            else:
                #logging.error("314 Trying re on field 502 for %s" % record.title())
                thesis_re = re.compile(r"Thesis")
                #! Quick hack to check for "Thesis" string in 502
                if record['502']:
                    desc502 = record['502'].value()
                else:
                    desc502 = ''
                if thesis_re.search(desc502):
                    format = 'Thesis'
                else:
                    format = 'Manuscript'
        else:
            format = 'Manuscript'
    # checks 006 to determine if the format is a manuscript
    if record['006'] and len(format) < 1:
        field006 = record['006'].value()
        if field006[0] == 't':
            format = 'Manuscript'
        elif field006[0] == 'm' or field006[6] == 'o':
            #! like to use field006[9] to further break-down Electronic format
            format = 'Electronic'
    # Doesn't match any of the rules
    if len(format) < 1:
        #logging.error("309 UNKNOWN FORMAT Title=%s Leader: %s" % (record.title(),leader))
        format = 'Unknown'

    # Some formats are determined by location
    
    format = lookup_location(record,format)
    return format

lc_stub_search = re.compile(r"([A-Z]+)")

def get_lcletter(record):
    '''Extracts LC letters from call number.'''
    lc_descriptions = []
    if record['050']:
        callnum = record['050'].value()
    elif record['090']: # Per CC's practice
        callnum = record['090'].value()
    else:
        return None,lc_descriptions
    lc_stub_result = lc_stub_search.search(callnum)
    if lc_stub_result:
        code = lc_stub_result.groups()[0]
        try:
            lc_descriptions.append(marc21_maps.LC_CALLNUMBER_MAP[code])
        except:
            pass
        return code,lc_descriptions
    return None,lc_descriptions

def get_carl_location(record):
    """
    Uses 945 field to extract library code, bib number, and item number
    from record

    :param record: MARC21 record
    """
    output = {}
    field945 = record['945']
    if field945 is not None:
        subfield_a = field945['a']
        if subfield_a is not None:
            data = subfield_a.split(" ")
            output['site-code'] = data[0]
            output['ils-bib-number'] = data[1]
            output['ils-item-number'] = data[2]
    return output
    

def get_cc_location(record):
    """Uses CC's location codes in Millennium to map physical
    location of the item to human friendly description from 
    the tutt_maps LOCATION_CODE_MAP dict"""
    output = []
    if record['994']:
        locations = record.get_fields('994')
    else:
        locations = []
    for row in locations:
        try:
            locations_raw = row.get_subfields('a')
            for code in locations_raw:
                code = LOCATION_RE.sub("",code)
                output.append((code,tutt_maps.LOCATION_CODE_MAP[code]))
                ##if code in tutt_maps.SPECIAL_COLLECTIONS:
                ##    output.append((code,"Special Collections"))
                ##if code in tutt_maps.GOVDOCS_COLLECTIONS:
                ##    output.append("Government Documents")
        except KeyError:
#            logging.info("%s Location unknown=%s" % (record.title(),locations[0].value()))
            output.append(('Unknown','Unknown'))
    return output

def get_subject_names(record):
    """
    Iterates through record's 600 fields, returns a list of names
 
    :param record: MARC record, required
    :rtype: List of subject terms
    """
    output = []
    subject_name_fields = record.get_fields('600')
    for field in subject_name_fields:
        name = field.get_subfields('a')[0]
        titles = field.get_subfields('c')
        for title in titles:
            name = '%s %s' % (title,name)
        numeration = field.get_subfields('b')
        for number in numeration:
            name = '%s %s' % (name,number)
        dates = field.get_subfields('d')
        for date in dates:
            name = '%s %s' % (name,date)
        output.append(name)
    return output

def lookup_location(record,format=None):
    """
    Does a look-up on location to determine format for edge cases like annuals in the 
    reference area.

    :param record: MARC Record
    :param format: current format
    """
    location_list = locations = record.get_fields('994')
    for location in location_list:
         subfield_a = str(location['a'])
         in_reference = REF_LOC_RE.search(subfield_a)
         if in_reference is not None:
              ref_loc_code = in_reference.groups()[0]
              if ref_loc_code != 'tarfc':
                  return "Book" # Classify everything as a book and not journal
         in_periodicals = PER_LOC_RE.search(subfield_a)
         if in_periodicals is not None:
             return "Journal" 
    return format

def parse_008(record, marc_record):
    """
    Function parses 008 MARC field 

    :param record: Dictionary of MARC record values
    :param marc_record: MARC record
    """
    if marc_record['008']:
        field008 = marc_record['008'].value()
        if len(field008) < 20:
            print("FIELD 008 len=%s, value=%s bib_#=%s" % (len(field008),
                                                           field008,
                                                           record["id"]))
        # "a" added for noninteger search to work
        dates = (field008[7:11] + 'a', field008[11:15] + 'a')
        # test for which date is more precise based on searching for
        # first occurence of nonintegers, i.e. 196u > 19uu
        occur0 = NONINT_RE.search(dates[0]).start()
        occur1 = NONINT_RE.search(dates[1]).start()
        # if both are specific to the year, pick the earlier of the two
        if occur0 == 4 and occur1 == 4:
            date = min(dates[0], dates[1])
        else:
            if dates[1].startswith('9999'):
                date = dates[0]
            elif occur0 >= occur1:
                date = dates[0]
            else:
                date = dates[1]
        # don't use it if it starts with a noninteger
        if NONINT_RE.match(date):
            record['pubyear'] = ''
        else:
            # substitute all nonints with dashes, chop off "a"
            date = NONINT_RE.sub('-', date[:4])
            record['pubyear'] = date
            # maybe try it as a solr.DateField at some point
            #record['pubyear'] = '%s-01-01T00:00:01Z' % date
    
        audience_code = field008[22]
        if audience_code != ' ':
            try:
                record['audience'] = marc_maps.AUDIENCE_CODING_MAP[audience_code]
            except KeyError as error:
                #sys.stderr.write("\nIllegal audience code: %s\n" % error)
                record['audience'] = ''

        language_code = field008[35:38]
        try:
            record['language'] = marc_maps.LANGUAGE_CODING_MAP[language_code]
        except KeyError:
            record['language'] = ''
    return record
