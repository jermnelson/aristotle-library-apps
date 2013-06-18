"""
 :mod:`redis_helpers` Redis Title Search Helpers
"""
__author__ = "Jeremy Nelson"

import random
try:
    import aristotle.lib.metaphone as metaphone
except ImportError:
    import metaphone

# Stopwords extracted from nltk.corpus.stopwords.words('english')
STOPWORDS = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
             'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
             'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
             'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
             'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am',
             'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
             'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
             'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
             'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
             'through', 'during', 'before', 'after', 'above', 'below', 'to',
             'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
             'again', 'further', 'then', 'once', 'here', 'there', 'when',
             'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
             'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
             'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
             'can', 'will', 'just', 'don', 'should', 'now']


def add_title(raw_title, title_metaphone, redis_server):
    #title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
    title_pipeline = redis_server.pipeline()
    title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))
    redis_server.sadd(title_metaphone, title_key)
    redis_server.hset(title_key, "phonetic", title_metaphone)
    redis_server.hset(title_key, "raw", raw_title)
    return title_key

#def add_title(raw_title,redis_server):
#    title_pipeline = redis_server.pipeline()
#    title_key = "rda:Title:{0}".format(redis_server.incr("global rda:Title"))



def add_metaphone_key(metaphone, title_keys, redis_server):
    metaphone_key = "all-metaphones:{0}".format(metaphone)
    for title_key in title_keys:
        redis_server.sadd(metaphone_key, title_key)
    title_pipeline.execute()


def add_or_get_metaphone_title(raw_title, redis_server):
    stop_metaphones, all_metaphones, title_metaphone = process_metaphone_title(raw_title)
    title_metaphone_key = 'title-metaphones:{0}'.format(title_metaphone)
    title_key = add_title(raw_title,
                          title_metaphone,
                          redis_server)
    redis_server.sadd(title_metaphone_key,
                      title_key)

    title_keys = redis_server.smembers(title_metaphone_key)
    for row in all_metaphones:
        add_metaphone_key(row, title_keys, redis_server)
    for row in stop_metaphones:
        add_metaphone_key(row, title_keys, redis_server)
    return title_keys


def generate_title_app(work, redis_server):
    """
    Helper function takes a BIBFRAME CreativeWork with a title, creates
    supporting Redis datastructures for the title app

    :param work: BIBFRAME Work
    :parm redis_server: Redis server
    """
    if not getattr(work,'title') or work.title is None:
        return
    raw_title = work.title.get('rda:preferredTitleForTheWork')
    terms, normed_title = process_title(raw_title)
    title_key = 'title-normed:{0}'.format(normed_title)
    work.title['normed'] = normed_title
    redis_server.sadd(title_key,work.redis_key)
    for term in terms:
        redis_server.sadd('title-normed:{0}'.format(term),
                          work.redis_key)
    redis_server.zadd('z-titles-alpha',
                      0,
	              normed_title)
    work.save()



def generate_title_app_metaphone(work, redis_server):
    """
    Helper function takes a BIBFRAME CreativeWork with a title, creates
    supporting Redis datastructures for the title app

    :param work: BIBFRAME Work
    :parm redis_server: Redis server
    """
    if not 'rda:Title' in work.attributes:
        #print('''Work w/ redis-key={0} w/o a title.
        #         Values:{1}'''.format(work.redis_key, work.attributes))
        return
    raw_title = work.attributes['rda:Title']['rda:preferredTitleForTheWork']
    stop_metaphones, all_metaphones, title_metaphone = process_title(raw_title)
    title_metaphone_key = 'first-term-metaphones:{0}'.format(all_metaphones[0])
    first_word_key = 'first-word:{0}'.format(raw_title.split(" ")[0].lower())
    redis_server.sadd(title_metaphone_key, work.redis_key)
    redis_server.sadd(first_word_key, work. redis_key)
    work.attributes['rda:Title']['phonetic'] = title_metaphone
    if 'rda:variantTitleForTheWork:sort' in work.attributes:
        redis_server.zadd("z-titles-alpha",
            0,
            work.attributes['rda:Title'].get('rda:variantTitleForTheWork:sort')
            )
    else:
        redis_server.zadd("z-titles-alpha",
            0,
            work.attributes['rda:Title'].get('rda:preferredTitleForTheWork'))
    for row in all_metaphones:
        add_metaphone_key(row, [work.redis_key, ], redis_server)
    for row in stop_metaphones:
        add_metaphone_key(row, [work.redis_key, ], redis_server)
    work.save()


def process_title(raw_title):
    """
    Function takes a raw title, removes stopwords and punctuation, converts
    all terms into uppercase utf8 encoded strings and associates each
    Creative Work Redis key with the term's set.

    :param raw_title: Raw title
    """
    if raw_title is None:
        return [], None
    raw_terms, terms = raw_title.split(" "), []
    
    for term in raw_terms:
        if term.lower() not in STOPWORDS: 
	    for punc in [",",".",";",":","'",'"',"/"]:
	        term = term.replace(punc,"")
            try:
                term = term.decode('utf-8', 'ignore')
            except UnicodeEncodeError, e:
                pass
            if len(term.strip()) > 0:
                terms.append(term.strip().upper())
    title_key = ''.join(terms)
    return terms, title_key

    

def process_metaphone_title(raw_title):
    """
    Function takes a raw_title, removes any stopwords from the beginning,
    extracts the metaphone for the terms in the title and returns
    a list of primary phonetics, a list of alternative phonetics, and
    the title as phonetic phrase with spaces between words.

    :param raw_title: Raw title
    """
    stop_metaphones, all_metaphones = [], []
    raw_terms, terms = raw_title.split(" "), []
    for term in raw_terms:
        term = term.lower()
        first_phonetic, second_phonetic = metaphone.dm(term.decode('utf8',
                                                                  "ignore"))

        if term not in STOPWORDS:
            stop_metaphones.append(first_phonetic)
        all_metaphones.append(first_phonetic)
    title_metaphone = ''.join(all_metaphones)
    return stop_metaphones, all_metaphones, title_metaphone



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

def index_title(title_entity, redis_datastore):
    """Takes a TitleEntity, process title, and indexes into datastore

    Parameters:
    title_entity -- bibframe.models.TitleEntity
    redis_datastore -- Redis instance or Redis Cluster
    """
    if title_entity.redis_key is None:
        title_entity.save()
    terms, normed_title = process_title(title_entity.label)
    title_normed_key = 'title-normed:{0}'.format(normed_title)
    redis_datastore.sadd(title_normed_key, title_entity.redis_key)
    redis_datastore.zadd('z-titles-alpha',
                         0,
                         normed_title)
    title_keys = ["title-normed:{0}".format(x.encode('utf-8', 'ignore'))
                  for x in terms]
    for key in list(set(title_keys)):
        redis_datastore.sadd(key, title_entity.redis_key)
    
                             

def search_title(user_input, redis_server):
    work_keys = []
    terms, normed_title = process_title(user_input)
    # Exact match on normed title, return work keys
    # associated with normed title key
    #if redis_server.exists("title-normed:{0}".format(normed_title)):
    #    return list(redis_server.smembers("title-normed:{0}".format(normed_title)))

    # If the terms list is null, tries to norm user_input, for edge cases where
    # the user input for the title could be a single, stop-word
    if len(terms) < 1:
        title_keys = ["title-normed:{0}".format(user_input.lower().strip()), ]        
    else:
        title_keys = ["title-normed:{0}".format(x.encode('utf-8', 'ignore')) for x in terms]
    for title_key in redis_server.sinter(title_keys):
        related_works = redis_server.smembers("{0}:relatedResources".format(title_key))
        for work_key in related_works:
            work_keys.append(work_key)
    return work_keys

def search_title_metaphone(user_input,redis_server):
    title_keys = []
    metaphones, all_metaphones, title_metaphone = process_metaphone_title(user_input)
    metaphone_keys = ["all-metaphones:{0}".format(x) for x in all_metaphones]
##    metaphone_keys.append('first-term-metaphones:{0}'.format(all_metaphones[0]))
    metaphone_keys.append(
        'first-word:{0}'.format(user_input.split(" ")[0].lower()))
    temp_key = "tmp:{0}".format(random.random())
    redis_server.sinterstore(temp_key, metaphone_keys)
    title_keys = redis_server.sort(temp_key,
        by="*:rda:Title->sort",
        alpha=True)
    redis_server.expire(temp_key, 15)
##    typeahead_keys = typeahead_search_title(user_input,redis_server)
##    if typeahead_keys is not None:
##        all_keys = list(title_keys)
##        all_keys.extend(typeahead_keys)
##    else:
##        all_keys = title_keys
    return title_keys
##    return all_keys









