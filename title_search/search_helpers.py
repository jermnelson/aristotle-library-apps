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
    def add_title():
        title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
        title_pipeline.sadd(title_metaphone,title_key)
        title_pipeline.hset(title_key,"phonetic",title_metaphone)
        title_pipeline.hset(title_key,"raw",raw_title)
        return title_key
    stop_metaphones,all_metaphones,title_metaphone = process_title(raw_title)
    title_pipeline = redis_server.pipeline()
    if not redis_server.hexists('h-title-metaphones',title_metaphone):
        
        redis_server.hset('h-title-metaphones',title_metaphone)
            
    
   
    

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

def add_marc_title(title_field,redis_server):
    """
    Function takes a MARC21 title field, extracts the title information
    from subfields and creates a sort title depending on second indicator

    :param title_field: MARC21 field
    :param redis_server: Title Redis instance
    """
    if title_field.tag not in ['210','222','240','242','243',
                               '245','246','247']:
        raise ValueError("{0} not a title field".format(title_field.tag))
    raw_title = ' '.join(title_field.get_subfields('a','b'))
    title_key = add_or_get_title(raw_title,redis_server)
    if int(title_field.indicators[1]) > 0:
        nonfiling_offset = int(title_field.indicators[1])
        sort_title = raw_title[nonfiling_offset:]
        redis_server.hset(title_key,"sort",sort_title)
        
    
    
        
                              
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
##    title_metaphone = metaphone.dm(raw_title.decode('utf8',
##                                                    "ignore"))[0]
    title_metaphone = ''.join(all_metaphones)
    return stop_metaphones,all_metaphones,title_metaphone
        
def search_title(user_input,redis_server):
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
    if redis_server.exists(title_metaphone):
        title_keys = list(redis_server.smembers(title_metaphone))
    else:
        phonetic_keys = redis_server.keys("{0}*".format(title_metaphone))
        # Recursive call, eliminates last character from string and
        # returns the result from call func again
        if len(phonetic_keys) < 1:
            truncated_input = user_input[:-1]
            return search_title(truncated_input,redis_server)
        else:
            for phonetic_key in phonetic_keys:
                for title_key in redis_server.smembers(phonetic_key):
                    title_keys.append(title_key)
    return title_keys
            
            
        
        
    
    
        
    
    
