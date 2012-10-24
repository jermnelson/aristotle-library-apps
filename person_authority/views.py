"""
 mod:`urls` Person Authority App URL routing
"""
__author__ = "Jeremy Nelson"
from app_settings import APP
from django.views.generic.simple import direct_to_template
from aristotle.views import json_view
from aristotle.settings import AUTHORITY_REDIS,INSTANCE_REDIS,WORK_REDIS
from redis_helpers import process_name
from marcr.app_helpers import get_brief

authority_redis = AUTHORITY_REDIS

def app(request):
    """
    Default view for Person Authority App
    """
    return direct_to_template(request,
                              'person_authority/app.html',
                              {'app':APP})
                               

@json_view
def search(request):
    """
    JSON search view returns the results of searching the Authority Redis
    datastore.

    :param request: HTTP Request
    """
    output = []
    raw_name = request.REQUEST.get("q")
    person_metaphones = process_name(raw_name)
    metaphone_keys = ["person-metaphones:{0}".format(x) for x in person_metaphones]
    join_operation = request.REQUEST.get("bool","AND")
    if join_operation == "OR":
        person_keys = authority_redis.sunion(metaphone_keys)
    else: # Default is an AND search
        person_keys = authority_redis.sinter(metaphone_keys)
        all_work_keys = authority_redis.sunion(["{0}:rda:isCreatorPersonOf".format(x) for x in person_keys])
    for work_key in all_work_keys:
        brief_rec = get_brief(redis_work=WORK_REDIS,
                              redis_instance=INSTANCE_REDIS,
                              redis_authority=authority_redis,
                              work_key=work_key)
        brief_rec['search_prefix'] = raw_name
        output.append(brief_rec)
    return {'results':output}
    
    
