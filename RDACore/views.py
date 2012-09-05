"""
 :mod:`views` Views for RDA Core Discovery App
"""
__author__ = "Jeremy Nelson"

from django.views.generic.simple import direct_to_template
from django.http import Http404,HttpResponse,HttpResponseRedirect
from aristotle.settings import INSTITUTION
from app_settings import APP,FACETS
from redis_helpers import get_facets

def default(request):
    """
    Displays default view of the RDA Core Discovery App

    :param request: HTTP Request
    """
    facets = []
    for entity in ["Work",
                   "Expression",
                   "Manifestation",
                   "Item",
                   "Person",
                   "CorporateBody"]:
        
        facets.append({"name":entity,
                       "facets":get_facets(entity)})
##    facets = [{"name":"Work","facets":[{"label":"date of work",
##                                         "count":25,
##                                        "members":["2012 (5)",
##                                                  "2011 (3)",
##                                                  "2010 (7)"]},
##                                        {"label":"form of work",
##                                         "count":3}]},
##              {"name":"Expression","facets":[{"label":"content type",
##                                               "count":10},
##                                              {"label":"date of expression",
##                                               "count":25}]},
##              {"name":"Manifestation","facets":[{"label":"carrier type",
##                                                 "count":4},
##                                                {"label":"copyright date",
##                                                 "count":25}]},
##              {"name":"Item","facets":[{"label":"restrictions on use",
##                                        "count":10}]}]
               
                                        
    return direct_to_template(request,
                              'rda-core-app.html',
                              {'app':APP,
                               'facets':facets,
                               'institution':INSTITUTION})
                               
