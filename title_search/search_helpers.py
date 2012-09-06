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
    metaphones,alt_metaphones,title_metaphone = process_title(raw_title)
    # Very primitive, checks if title_metaphone exists, if does checks value
    # of title_metaphone with value in datastore, returns rda:Title if present
    # or creates a new title_key
    if redis_server.hexists('h-title-metaphone',title_metaphone):
        tmp_redis_key = redis_server.hget('h-title-metaphone',title_metaphone)
        if redis_server.hget(tmp_redis_key,"raw") == raw_title:
            title_key = tmp_redis_key
        else:
            title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
            
    else:
        title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
    title_pipeline = redis_server.pipeline()
    title_pipeline.hset(title_key,"raw",raw_title)
    title_pipeline.hset(title_key,"phonetic",title_metaphone)
    redis_server.hset('h-title-metaphone',title_metaphone,title_key)
    
    for phonetic in metaphones + alt_metaphones:
        phonetic_key = "title-phonetic:{0}".format(phonetic)
        title_pipeline.sadd(phonetic_key,title_key)
        title_pipeline.zadd('z-title-phonetic',0,phonetic_key)
    term_incr = ''
    for phonetic in metaphones:
        term_incr += " {0}".format(phonetic)
        title_pipeline.zadd('z-title-phonetic-build',0,term_incr.strip())
    
    title_pipeline.execute()        
        
                              
def process_title(raw_title):
    """
    Function takes a raw_title, removes any stopwords from the beginning,
    extracts the metaphone for the terms in the title and returns
    a list of primary phonetics, a list of alternative phonetics, and
    the title as phonetic phrase with spaces between words.

    :param raw_title: Raw title
    """
    raw_terms,terms = raw_title.split(" "),[]
    for term in raw_terms:
        term = term.lower()
        if term not in STOPWORDS:
            terms.append(term)
    
    metaphones,alt_metaphones = [],[]
    for term in terms:
        first_phonetic,second_phonetic = metaphone.dm(term.decode('utf8'))
        if len(first_phonetic) > 0:
            metaphones.append(first_phonetic.strip())
        if len(second_phonetic) > 0:
            alt_metaphones.append(second_phonetic.strip())
    title_metaphone = " ".join(metaphones)
    return metaphones,alt_metaphones,title_metaphone
        
def search_title(user_input,redis_server):
    """
    Function attempts to find a match first with title_metaphone phrase,
    followed by a union of each of the metaphones. Finally, if no hits,
    starts from the first metaphone and progressively checks each from zset
    z-title-phonetic-build.

    :param user_input: User input
    :param redis_server: Title Redis instance
    :rtype list: Redis key of title
    """
    metaphones,alt_metaphones,title_metaphone = process_title(raw_title)
    # First checks if title_metaphone already exists
    if redis_server.hexists('h-title-metaphone',title_metaphone):
        title_redis_key = redis_server.hget('h-title-metaphone',title_metaphone)
        return [title_redis_key,]
    # Second, checks intersection of each title phonetically title-key set
    phonetic_keys = []
    for metaphone in metaphones:
        phonetic_keys.append("title-phonetic:{0}".format(metaphone))
    intersection_title_keys = redis_server.sinter(phonetic_keys)
    if len(intersection_title_keys) > 0:
        return list(intersection_title_keys)
    # Third, checks intersection of each title in the phonetically alternate
    # in the title-key set
    alt_phonetic_keys = []
    for metaphone in alt_metaphones:
        alt_phonetic_keys.append("title-phonetic:{0}".format(metaphone))
    intersection_title_keys = redis_server.sinter(alt_phonetic_keys)
    if len(intersection_title_keys) > 0:
        return list(intersection_title_keys)
    # Forth, iterates through metaphones, building up and then checking each
    # increment if it exists already in datastore
    nearby_keys = []
    title_phonetics = []
    for metaphone in metaphones:
        title_phonetics.append(metaphone)
        title_incr = ' '.join(title_phonetics)
        rank = redis_server.zrank('z-title-phonetic-build',title_incr)
        if rank is None:
            return nearby_keys
        else:
            if redis_server.hexists('h-title-metaphone',title_incr):
                nearby_keys.append(redis_server.hget('h-title-metaphone',title_incr))
    return None
            
            
        
        
    
    
        
    
    
