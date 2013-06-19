"Views for Dashboard App in the Aristotle Library Apps Django Environment"
__author__ = "Jeremy Nelson"

from aristotle.settings import INSTITUTION, REDIS_DATASTORE
from dashboard.instruments import BibframePieChart, WordCloud
from django.shortcuts import render

def app(request):
    "Default view for Dashboard"

    return render(request, 
                  'home.html',
                  {})
