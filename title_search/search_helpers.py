"""
 :mod:`title_search_helpers` Redis Title Search
"""
__author__ = "Jeremy Nelson"

import redis,sys
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

def add_or_get_title(raw_title,redis_server):
    """
    Function takes a raw_title, checks if value exists "as is"
    along with a stopword and metaphone checks in datastore.
    
    Returns existing rda:Title key or
    :param raw_title: Raw title either extracted from record source
                      or from submission by user
    """
    raw_terms,terms = raw_title.split(" "),[]
    for term in raw_terms:
        term = term.lower()
        if term not in STOPWORDS:
            terms.append(term)
    
    metaphones,alt_metaphones = [],[]
    for term in terms:
        first_phonetic,second_phonetic = metaphone.dm(term.decode('utf8'))
        metaphones.append(first_phonetic)
        if len(second_phonetic) > 0:
            alt_metaphones.append(second_phonetic)
    title_metaphone = " ".join(metaphones)
    # Very primitive, checks if title_metaphone exists, if does checks value
    # of raw_title with value in datastore, returns rda:Title if present
    # or creates a new title_key
    if redis_server.hexists('h-title-metaphone',title_metaphone):
        tmp_redis_key = redis_server.hget('h-title-metaphone',title_metaphone)
        if redis_server.hget(tm_redis_key,"raw") == raw_title:
            title_key = tmp_redis_key
        else:
            title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
            
    else:
        title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
    redis_server.hset(title_key,"raw",raw_title)
    title_pipeline = redis_server.pipeline()
    for phonetic in metaphones + alt_metaphones:
        phonetic_key = "title-phonetic:{0}".format(phonetic)
        title_pipeline.sadd(phonetic_key,title_key)
        title_pipeline.zadd('z-title-phonetic',0,phonetic_key)
    term_incr = ''
    for phonetic in metaphones:
        term_incr += " {0}".format(phonetic)
        title_pipeline.zadd('z-title-phonetic-build',0,term_incr.strip())
    title_pipeline.execute()
    
    
                
    
        
        
                              
def ingest_title(raw_title,redis_server):
    """
    Function takes a raw_title, removes any stopwords from the beginning,
    extracts the metaphone for the terms in the title, saves each metaphone
    as a Redis set.

    :param raw_title: Raw title
    :param redis_server: Redis server
    """
    #rda_key = redis_server.incr("global rda:Title")

    for term in terms:
        metaphones = metaphone.dm(term)
        
        
    
