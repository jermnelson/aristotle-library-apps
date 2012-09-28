__author__ = "Diane Westerfield"
__author__ = "Jeremy Nelson"
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse

def app(request):
    """
    Returns responsive app view for DBFinder App
    """
    return HttpResponse("In dbfinder app")
    
