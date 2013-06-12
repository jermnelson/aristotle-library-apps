"""
 :mod:`ingesters` Module ingests MARC21 and MODS records into a MARCR-Redis datastore
 controlled by the MARCR app.
"""
__author__ = "Jeremy Nelson"

import datetime, re, pymarc, os, sys,logging, redis, time
from aristotle.settings import PROJECT_HOME, REDIS_DATASTORE
import json

HONORIFIC_PREFIXES = ['Ms',
 'Miss',
 'Mrs',
 'Mr',
 'Master',
 'Rev',
 'Fr',
 'Dr',
 'Atty',
 'Prof',
 'Hon',
 'Pres',
 'Gov',
 'Coach',
 'Ofc']

HONORIFIC_SUFFIXES = ['M.A.',
                      'M.S.',
                     'M.F.A.',
                     'LL.M',
                     'M.L.A.',
                     'M.B.A.',
                     'M.Sc',
                     'J.D.',
                     'M.D.',
                     'D.O.',
                     'Pharm.D.',
                     'Ph.D.',
                     'I',
                     'II',
                     'III',
                     'IV',
                     'V']

DATE_RE = re.compile(r"(\d+\w*)-*(\d*\w*)")
def personal_name_parser(name_string):
    """Function parses a name and returns a dict of names

    This function takes a personal name in the following format:
    Last name, first name middle name, YYYY-YYYY. See unit tests
    for different name variations that can be parsed with this
    function.
    
    Parameters:
    name_string -- Name String in standard bibliographic uniform
                   format
    """
    
    person = {'rda:preferredNameForThePerson': name_string}
    all_names = filter(lambda x: len(x) > 0,
                       [name.strip() for name in ' '.join(name_string.split(",")).split(" ")])
    person['schema:familyName'] = all_names.pop(0)
    remaining_names = []
    while len(all_names) > 0:
        name = all_names.pop(0)
        if HONORIFIC_PREFIXES.count(name) > 0:
            person['schema:honorificPrefix'] = name
        elif HONORIFIC_SUFFIXES.count(name) > 0:
            person['schema:honorificSuffix'] = name
        elif DATE_RE.search(name) is not None:
            dates = DATE_RE.search(name).groups()
            person['rda:dateOfBirth'] = dates[0]
            if len(dates) > 1:
                person['rda:dateOfDeath'] = dates[1]
        else:
            remaining_names.append(name)
    if len(remaining_names) > 0:
        person['schema:givenName'] = remaining_names.pop(0)
    if len(remaining_names) > 0:
        for row in remaining_names:
            if person.has_key('schema:additionalName'):
                person['schema:additionalName'] += ' {0}'.format(row)
            else:
                person['schema:additionalName'] = row
    return person

class Ingester(object):
    "Base Ingester class for ingesting metadata and bibliographic record"
    
    def __init__(self, **kwargs):
        """Initializes Ingester
        

        Keywords:
        redis_datastore -- StrictRedis or RedisCluster instance
        """
        self.redis_ds = kwargs.get('redis_datastore',
                                   REDIS_DATASTORE)

    def ingest(self):
        pass # Should be overridden by child classes



