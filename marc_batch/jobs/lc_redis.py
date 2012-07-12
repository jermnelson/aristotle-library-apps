"""
 :mod:`lc_redis` Module creates or validates Library of Congress Subject
 Headings and stores in 

"""
import redis,os,urllib2,urllib
try:
    import aristotle.settings as settings
    redis_server = redis.StrictRedis(host=settings.REDIS_ACCESS_HOST,
                                     port=settings.REDIS_ACCESS_PORT)
except ImportError:
    # For local development and outside of Aristotle Library Apps environment
    redis_server = redis.StrictRedis()
    

class LCSHIngester(object):
    """LCSHIngester class takes a MARC record, extracts and validates 6xx
    fields, and creates supporting Redis data structures.
    """

    def __init__(self,**kwargs):
        self.marc_record = kwargs.get('record')
        if kwargs.has_key('redis_server'):
            self.redis_server = kwargs.get('redis_server')
        else:
            self.redis_server = redis_server
        self.topical_base_url = 'http://id.loc.gov/authorities/label/{0}'
        self.geo_base_url = 'http://id.loc.gov/authorities/geographic/{0}'
        self.__validate650__()
##        self.__validate651__()

    def __process_geographic__(self,subfields):
        """Method takes a list of subfiel, queries LOC id service,
        and either adds or checks if term exists in Redis datastore,
        returns the Redis key for the geographic name

        :param subfields: List of 'a' or 'z' subfields
        """
        for subfield in subfields:
            loc_url = self.geo_base_url.format(urllib.quote(subfield))
        


    def __process_topical__(self,subfields):
        """Method takes a list of subfield a, queries LOC id service,
        and either adds or checks if term exists in Redis datastore,
        returns the Redis key for the topical term

        :param subfields: List of 'a' subfields
        """
        for subfield in subfields:
            pass

    def __validate650__(self):
        """Method extracts all 650 fields from MARC record, checks to
        see if it LCSH, and the calls the id.loc.gov website to extract
        the URI to associated the LCSH"""
        all650s = self.marc_record.get_fields('650')
        for field in all650s:
            if field.indicators[1] != '0':
                pass
            topical_key = self.__process_topical__(field.get_subfields('a'))
            geo_key = self.__process_geographic__(field.get_subfields('z'))

    


    
            
        
        
        
