"""
 mod:`urls` Catalog URL routes
"""
__author__ = "Jeremy Nelson"

from django.conf.urls import *
import discovery.views

urlpatterns = patterns('catalog.views',
    url(r"$^", "app", name="catalog-default"),
    url(r"^save$", "save", name="catalog-save"),
    url(r"^search$", "search", name="catalog-search"),
)


