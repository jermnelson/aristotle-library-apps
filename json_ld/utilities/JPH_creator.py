__author__ = "Jeremy Nelson"

import csv
import datetime
import json
import urllib2

from json_ld.utilities.creator import JSONLinkedDataCreator



class JohnPeabodyHarringtonJSONLinkedDataCreator(JSONLinkedDataCreator):
    CC_URI = 'http://id.loc.gov/authorities/names/n84168445'
    LOC_URI = 'http://id.loc.gov/authorities/names/no2008011986'
    

    def __init__(self,
                 creator_id=None, 
                 csv_filename=None):
        """Initializes instance of John Peabody Harrington JSON-LD creator

        Parameters:
        creator_id -- LOC ID of creator, defaults to Colorado College
        csv_filename -- Filename of CSV file, defaults to None
        """
        if creator_id is None:
            creator_id = self.CC_URI
        super(JohnPeabodyHarringtonJSONLinkedDataCreator, self).__init__(
            **{'creator_id': creator_id})
        self.title_prefix = 'John P. Harrington Papers 1907-1959 (some earlier)'
        jph_csv_reader = csv.DictReader(open(csv_filename, 'rb'))
        for row in jph_csv_reader:
            self.records.append(row)

    def __generate_topics__(self,
                            lcsh_subjects,
                            work_dict):
        """Internal function generates a list of topics from
        a list of LCSH uri

        Parameters:
        lcsh_subjects -- list of http://id.loc.gov subject uri
        work_dict -- Dictionary of properties for the Creative Work
        """
        if len(lcsh_subjects) > 0:
            print("Generate topics: {0}".format(len(lcsh_subjects)))
            work_dict['bf:subject'] = []
            for subject_uri in lcsh_subjects:
                uri = subject_uri.replace('"','').strip()
                
                if not self.topics.has_key(uri):
                    loc_uri = json.load(
                        urllib2.urlopen('{0}.json'.format(uri)))
                    loc_key = u"<{0}>".format(uri)
                    self.topics[uri] = {
                        '@type': 'bf:Topic',
                        'prov:Generation': self.__generate_provenance__(),
                        'bf:label': loc_uri[loc_key].get(
                            u'<http://www.w3.org/2004/02/skos/core#prefLabel>',
                            [{'value':uri},])[0].get('value'),
                        'bf:identifier': uri,
                        'bf:hasAuthority': self.LOC_URI} 
                    lcc_classification = loc_uri[loc_key].get(
                        u'<http://www.loc.gov/mads/rdf/v1#classification>',
                        None)
                    if lcc_classification is not None:
                        class_value = lcc_classification[0].get('value')
                        if not work_dict.has_key('bf:class-lcc'):
                            work_dict['bf:class-lcc'] = [class_value, ]
                        else:
                            work_dict['bf:class-lcc'].append(class_value)
                work_dict['bf:subject'].append(self.topics[uri])
            return work_dict

    def generate(self):
        "Linked Data Cataloging for John Peabody Harrington Collection"
        for row in self.records:
            work_dict = self.__generate_work__(
                creative_work_class='bf:Manuscript')
            instance_dict = self.__generate_instance__()
            title_str = '{0} Microfilm {1}, Reel {2}'.format(
                self.title_prefix,
                row.get('Microfilm #'),
                row.get('Reel #'))
            title_parts = row.get('Title').replace('"','').split(",")            
            if len(title_parts) > 1:
                sub_titles = []
                for sub in title_parts:
                    sub = sub.strip()
                    sub_titles.append(sub)
                title_str = '{0} "{1}'.format(title_str,
                                              '", "'.join(sub_titles))
                title_str += '"'
            elif len(title_parts) == 1:
                title_str = "{0} {1}".format(title_str,
                                             title_parts[0])
            work_dict['bf:title'] = {'@type': 'bf:TitleEntity',
                                     'bf:titleValue': title_str,
                                     'bf:label': title_str}
            instance_dict['schema:contentUrl'] = '/pdf/{0}'.format(
                row.get('Filename'))
            work_dict['bf:hasInstance'] = [instance_dict,]
            work_dict['rda:dateOfPublicationManifestation'] = row.get('Publication Date')
            subjects = row.get('LCSH').split(",")
            work_dict = self.__generate_topics__(subjects, work_dict)
            self.works.append(work_dict)
