"""
 :mod:`redis_helpers` - Redis and other helper classes for the Bibliographic
 Framework App
"""
__author__ = "Jeremy Nelson"

import csv
from aristotle.settings import REDIS_DATASTORE

def get_brief(**kwargs):
    """
    Searches datastore and returns brief record from bibframe:CreativeWork,
    bibframe:Instance, and bibframe:Authority datastores

    :param redis_datastore: Redis bibframe:Work datastore
    :param redis_datastore: Redis bibframe:Instance datastore
    :param redis_datastore; Redis bibframe:Authority datastore
    :param creative_work_key: Redis bibframe:CreativeWork key
    :param instance_key: Redis bibframe:Instance key
    """
    output, work_key, instance_keys = {},None,[]
    redis_datastore = kwargs.get('redis_datastore',
                                 REDIS_DATASTORE)
    if kwargs.has_key('creative_work_key'):
        work_key = kwargs.get('creative_work_key')
    if kwargs.has_key('instance_key'):
        instance_keys.append(kwargs.get('instance_key'))
        if work_key is None:
            work_key = redis_datastore.hget(instance_keys[0],
                                            'instanceOf')
    else:
        if redis_datastore.hexists(work_key, 'hasInstance'):
            instance_keys = [redis_datastore.hget(work_key, 'hasInstance'), ]
        elif redis_datastore.exists("{0}:hasInstance".format(work_key)):
            instance_keys = redis_datastore.smembers("{0}:hasInstance".format(work_key))
        else:
            raise ValueError("Work doesn't have an Instance")
    work_title_key = redis_datastore.hget(instance_keys[0],
                                          'title')
    # Instance has a Title Entity linked to it
    if redis_datastore.exists(work_title_key):
        title_entity = redis_datastore.hgetall(work_title_key)
        raw_title = title_entity.get('titleValue')
        if title_entity.has_key('subtitle'):
            raw_title = "{0} {1}".format(raw_title,
                                         title_entity.get('subtitle'))
        output["title"] = unicode(raw_title,
                                  errors="ignore")
    # Title may be stored as a literal
    elif redis_datastore.hexists(instance_keys[0], "title"):
        output["title"] = unicode(redis_datastore.hget(instance_keys[0],
                                                       "title"),
                                  errors="ignore")
            
    output['ils-bib-numbers'] = []
    for instance_key in instance_keys:
        output['ils-bib-numbers'].append(redis_datastore.hget("{0}:rda:identifierForTheManifestation".format(instance_key),
                                                             'ils-bib-number'))
    output['creators'] = []
    creator_keys = redis_datastore.smembers("{0}:rda:creator".format(work_key))
    for creator_key in creator_keys:
        output['creators'].append(unicode(redis_datastore.hget(creator_key,
                                                               "rda:preferredNameForThePerson"),
                                          errors="ignore"))
    return output


def get_json_linked_data(redis_datastore, redis_key):
    """
    Function takes a redis_key and Redis instance, return JSON_LD of the
    BIBFRAME entity
    """
    ld_output = {"@context":{ "bf": "http://bibframe.org/vocab/",
                              "prov":"http://www.w3.org/ns/prov#",
                              "rda": "http://rdvocab.info",
                              "redis_key": None,
                              "result": None,
                              "schema":"http://schema.org/" }}
    ld_output['redis_key'] = redis_key
    for key, value in redis_datastore.hgetall(redis_key).iteritems():
        # Assumes all values not explictly starting with "rda", "prov",
        # or "schema" is part of the bf (bibframe) name-space
        ld_key = None
        if key == 'created_on':
            ld_output['prov:Generation'] = {'prov:atTime': value }
        if key.startswith('rda:')\
           or key.startswith('prov')\
           or key.startswith('schema'):
            ld_key = key
        else:
            ld_key = "bf:{0}".format(key)
        if ld_key is not None:
            try:
                ld_output[ld_key] = unicode(value)
            except UnicodeDecodeError, e:
                ld_output[ld_key] = unicode(value, 'iso_8859_1')
    return ld_output



