"""creator.py contains the base class for JSON Linked Data Creation"""
__author__ = "Jeremy Nelson"

import datetime
import json

class JSONLinkedDataCreator(object):
    CONTEXT = {'bf': 'http://bibframe.org/vocab/',
               'prov': 'http://www.w3.org/ns/prov#',
               'rda': 'http://rdvocab.info',
               'schema': 'http://schema.org/'}

    def __init__(self,
                 creator_id=None):
        """Initializes instance of base JSON-LD creator class

        Parameters:
        creator_id -- LOC ID of creator, defaults to None
        """
        self.creator_id = creator_id
        self.records, self.topics, self.works = [], {}, []
        

    def __generate_instance__(self):
        "Internal function returns an instance dict"
        return {'@type': 'bf:Instance',
                'rda:carrierTypeManifestation': 'online resource',
                'prov:Generation': self.__generate_provenance__()}

    def __generate_provenance__(self):
        "Internal function returns a provenance information"
        return {'prov:atTime': datetime.datetime.utcnow().isoformat(),
                'prov:wasGeneratedBy': self.creator_id}

    

    def __generate_work__(self,
                          creative_work_class='bf:Work'):
        """"Internal function returns a bf:Work or subclass with a default of
        bf:Work

        Parameters:
        creative_work_class -- BIBFRAME Creative Work class, defaults to
                               bf:Manuscript for this collection
        """
        return {'@context': self.CONTEXT,
                '@type': creative_work_class,
                'prov:Generation': self.__generate_provenance__()}

    def generate(self):
        "Method should be overridden by child classes"
        pass
