"""
 :mod:`title_search_helpers` Redis Title Search
"""
__author__ = "Jeremy Nelson"

import redis,sys,re
import hashlib,logging
try:
    import aristotle.lib.metaphone as metaphone
except ImportError:
    import metaphone

# Stopwords extracted from nltk.corpus.stopwords.words('english')
STOPWORDS = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
             'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
             'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
             'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
             'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is',
             'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
             'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
             'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
             'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
             'through', 'during', 'before', 'after', 'above', 'below', 'to',
             'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
             'again', 'further', 'then', 'once', 'here', 'there', 'when',
             'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few','more',
             'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
             'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
             'just', 'don', 'should', 'now']


def add_title(raw_title,title_metaphone,redis_server):
    title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
    title_pipeline = redis_server.pipeline()
    title_pipeline.sadd(title_metaphone,title_key)
    title_pipeline.hset(title_key,"phonetic",title_metaphone)
    title_pipeline.hset(title_key,"raw",raw_title)
    title_pipeline.execute()
    return title_key

def add_metaphone_key(metaphone,title_keys,redis_server):
    metaphone_key = "all-metaphones:{0}".format(metaphone)
    title_pipeline = redis_server.pipeline()
    for title_key in title_keys:
        title_pipeline.sadd(metaphone_key,title_key)
    title_pipeline.execute()


def add_or_get_title(raw_title,redis_server):
    stop_metaphones,all_metaphones,title_metaphone = process_title(raw_title)
    first_word = raw_title.split(" ")[0].lower()
    title_metaphone_key = 'title-metaphones:{0}'.format(title_metaphone)
    title_key = add_title(raw_title,
                          title_metaphone,
                          redis_server)
    redis_server.sadd(title_metaphone_key,
                      title_key)
    
    title_keys = redis_server.smembers(title_metaphone_key)
    for metaphone in all_metaphones:
        add_metaphone_key(metaphone,title_keys,redis_server)
    for metaphone in stop_metaphones:
        add_metaphone_key(metaphone,title_keys,redis_server)
    return title_keys
    

def old_add_or_get_title(raw_title,redis_server):
    """
    Function takes a raw_title, checks if value exists "as is"
    along with a stopword and metaphone checks in datastore.
    
    Returns existing rda:Title key or new key
    :param raw_title: Raw title either extracted from record source
                      or from submission by user
    """
    stop_metaphones,all_metaphones,title_metaphone = process_title(raw_title)
    title_pipeline = redis_server.pipeline()
    if redis_server.exists(title_metaphone):
        title_keys = redis_server.smembers(title_metaphone)
        raw_already_exists = False
        for title_key in title_keys:
            if raw_title == redis_server.hget(title_key,"raw"):
                raw_already_exists = True
                continue
        if raw_already_exists == False:
            title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
            title_pipeline.sadd(title_metaphone,title_key)
            title_pipeline.hset(title_key,"phonetic",title_metaphone)
            title_pipeline.hset(title_key,"raw",raw_title)
    else:
        title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
        title_pipeline.sadd(title_metaphone,title_key)
        title_pipeline.hset(title_key,"phonetic",title_metaphone)
        title_pipeline.hset(title_key,"raw",raw_title) 
    title_pipeline.execute()
    return title_key

slash_re = re.compile(r"/$")
def add_marc_title(marc_record,redis_server):
    """
    Function takes a MARC21 record, extracts the title information
    from subfields and creates a sort title depending on second indicator

    :param marc_record: MARC21 record
    :param redis_server: Title Redis instance
    """
    # Extract 245    
    title_field = marc_record['245']
    
    if title_field is not None:
        raw_title = ''.join(title_field.get_subfields('a'))
        if slash_re.search(raw_title):
            raw_title = slash_re.sub("",raw_title).strip()
        subfield_b = ' '.join(title_field.get_subfields('b'))
        if slash_re.search(subfield_b):
            subfield_b = slash_re.sub("",raw_title).strip()
        raw_title += subfield_b
        if raw_title.startswith("..."):
            raw_title = raw_title.replace("...","")
        title_keys = add_or_get_title(raw_title,redis_server)
        for title_key in title_keys:
            if raw_title == redis_server.hget(title_key,"raw"):
                indicator_one = title_field.indicators[1]
                try:
                    indicator_one = int(indicator_one)
                except ValueError:
                    indicator_one = 0
                if int(indicator_one) > 0:
                    nonfiling_offset = int(title_field.indicators[1])
                    sort_title = raw_title[nonfiling_offset:]
                    title_sha1 = hashlib.sha1(sort_title)
                    redis_server.zadd("z-titles-alpha",0,sort_title)
                    redis_server.hset(title_key,"sort",sort_title)
                    sort_stop,sort_all,sort_metaphone = process_title(sort_title)
                    redis_server.sadd("title-metaphones:{0}".format(sort_metaphone),
                                      title_key)
                else:
                    redis_server.zadd("z-titles-alpha",0,raw_title)
                    title_sha1 = hashlib.sha1(raw_title)
                
                # Adds title keys to set of title sha1 value
                redis_server.sadd("s-sha1:{0}".format(title_sha1.hexdigest()),
                                      title_key)
                # Set legacy bib id
                field907 = marc_record['907']
                if field907 is not None:
                    raw_bib_id = ''.join(field907.get_subfields('a'))
                    redis_server.hset(title_key,"legacy-bib-id",raw_bib_id[1:-1])        
    
    
    
def process_title(raw_title):
    """
    Function takes a raw_title, removes any stopwords from the beginning,
    extracts the metaphone for the terms in the title and returns
    a list of primary phonetics, a list of alternative phonetics, and
    the title as phonetic phrase with spaces between words.

    :param raw_title: Raw title
    """
    stop_metaphones,all_metaphones = [],[]
    raw_terms,terms = raw_title.split(" "),[]
    for term in raw_terms:
        term = term.lower()
        first_phonetic,second_phonetic = metaphone.dm(term.decode('utf8',
                                                                  "ignore"))
        
        if term not in STOPWORDS:
            stop_metaphones.append(first_phonetic)
        all_metaphones.append(first_phonetic)
    title_metaphone = ''.join(all_metaphones)
    return stop_metaphones,all_metaphones,title_metaphone

        
def typeahead_search_title(user_input,redis_server):
    """
    Function attempts to find a match first with title_metaphone phrase,
    followed by a union of each of the metaphones. Finally, if no hits,
    starts from the first metaphone and progressively checks for close
    matches

    :param user_input: User input
    :param redis_server: Title Redis instance
    :rtype list: Redis keys for title
    """
    title_keys = []
    metaphones,all_metaphones,title_metaphone = process_title(user_input)
    title_metaphone_key = "title-metaphones:{0}".format(title_metaphone)
    if redis_server.exists(title_metaphone_key):
        for title_key in redis_server.smembers(title_metaphone_key):
            title_keys.append(title_key)
    phonetic_keys = redis_server.keys("{0}*".format(title_metaphone_key))
    # Recursive call, eliminates last character from string and
    # returns the result from call func again
    if len(phonetic_keys) < 1:
        truncated_input = user_input[:-1]
        return search_title(truncated_input,redis_server)
    else:
        more_keys = []
        for phonetic_key in phonetic_keys:
            this_title_keys = redis_server.smembers(phonetic_key)
            if this_title_keys is not None:
                more_keys.extend(this_title_keys)
        title_keys.extend(more_keys)
    all_keys = set(title_keys)
    return list(all_keys)

def search_title(user_input,redis_server):
    title_keys = []
    metaphones,all_metaphones,title_metaphone = process_title(user_input)
##    metaphone_keys = ["all-metaphones:{0}".format(x) for x in all_metaphones]
##    title_keys = redis_server.sinter(metaphone_keys)
    typeahead_keys = typeahead_search_title(user_input,redis_server)
    if typeahead_keys is not None:
        all_keys = list(title_keys)
        all_keys.extend(typeahead_keys)
    else:
        all_keys = title_keys
##    return title_keys
    return all_keys
            
            
        
        
    
    
        
    
    
