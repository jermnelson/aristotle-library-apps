__author__ = "Jeremy Nelson"

from aristotle.views import json_view
from keyword_search import whoosh_helpers

@json_view
def search(request):
    "Searches Whoosh index with query terms"
    return {}
