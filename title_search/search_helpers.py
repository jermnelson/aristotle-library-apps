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

def generate_title_app(work,redis_server):
    """
    Helper function takes a MARCR Work with a title, creates supporting
    Redis datastructures to support the title app

    :param work: MARCR Work
    :parm redis_server: Redis server
    """
    if not work.attributes.has_key('rda:Title'):
        print("Work with redis-key={0} doesn't have a title.\n\tValues:{1}".format(work.redis_key,
                                                                                   work.attributes))
        return
    stop_metaphones,all_metaphones,title_metaphone = process_title(work.attributes['rda:Title']['rda:preferredTitleForTheWork'])
    title_metaphone_key = 'first-term-metaphones:{0}'.format(all_metaphones[0])
    title_pipeline = redis_server.pipeline()
    title_pipeline.sadd(title_metaphone_key,work.redis_key)
    work.attributes['rda:Title']['phonetic'] = title_metaphone
    if work.attributes['rda:Title'].has_key('rda:variantTitleForTheWork:sort'):
        title_pipeline.zadd("z-titles-alpha",0,work.attributes['rda:Title'].get('rda:variantTitleForTheWork:sort'))
    else:
        title_pipeline.zadd("z-titles-alpha",0,work.attributes['rda:Title'].get('rda:preferredTitleForTheWork'))
    for metaphone in all_metaphones:
        add_metaphone_key(metaphone,[work.redis_key,],redis_server)
    for metaphone in stop_metaphones:
        add_metaphone_key(metaphone,[work.redis_key,],redis_server)
    title_pipeline.execute()
    work.save()
        
    
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
    metaphone_keys = ["all-metaphones:{0}".format(x) for x in all_metaphones]
    metaphone_keys.append('first-term-metaphones:{0}'.format(all_metaphones[0]))
    title_keys = redis_server.sinter(metaphone_keys)
##    typeahead_keys = typeahead_search_title(user_input,redis_server)
##    if typeahead_keys is not None:
##        all_keys = list(title_keys)
##        all_keys.extend(typeahead_keys)
##    else:
##        all_keys = title_keys
    return title_keys
##    return all_keys
            
            
        
        
    
    
        
    
    
