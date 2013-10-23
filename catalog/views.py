__author__ = "Jeremy Nelson"

from django.http import HttpResponse
from django.shortcuts import render

from aristotle.views import json_view
from aristotle.settings import INSTITUTION
from app_settings import APP

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

@json_view
def search(request):
    return {'message': 'ok', 'instances': [{'id': 'bf:Instance:34'}]}
    


