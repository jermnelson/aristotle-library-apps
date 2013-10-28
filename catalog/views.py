__author__ = "Jeremy Nelson"

from django.http import HttpResponse
from django.shortcuts import render

from aristotle.settings import REDIS_DATASTORE
from aristotle.views import json_view
from aristotle.settings import INSTITUTION
from app_settings import APP

from keyword_search.whoosh_helpers import keyword_search

def app(request):
    """
    Default view for Catalog

    Parameters:
    request -- HTTP Request
    """
    return render(request,
                  'catalog/app.html',
                  {'APP': APP,
                   'INSTITUTION': INSTITUTION})

def display_cover_image(request, redis_id, type_of, image_ext):
    """
    Returns a cover image based on the CoverArt's redis key,
    if the type-of is body or thumbnail and the image_ext is
    either "jpg", "png", or "gif"
    
    :param redis_id: Redis key id of the bibframe:CoverArt 
    :param type_of: Should be either "thumbnail" or "body" 
    "param image_ext: The images extension
    """
    redis_key = "bf:CoverArt:{0}".format(redis_id)
    if type_of == 'thumbnail':
        raw_image = REDIS_DATASTORE.hget(redis_key, 
                                          'thumbnail')
    elif type_of == 'body':
        raw_image = REDIS_DATASTORE.hget(redis_key, 
                                          'annotationBody')
    if raw_image is None:
        raise Http404
    return HttpResponse(raw_image, 
                        mimetype="image/{0}".format(image_ext))

@json_view
def search(request):
    results = keyword_search(query_text=request.POST.get('q'))
    return {'message': 'ok', 'instances': results}

    


