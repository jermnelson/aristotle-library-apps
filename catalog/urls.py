"""
 mod:`urls` Catalog URL routes
"""
__author__ = "Jeremy Nelson"

from django.conf.urls import *
import discovery.views

urlpatterns = patterns('catalog.views',
    url(r"$^", "app", name="catalog-default"),
    url(r"^[c|C]over[A|_a]rt/(\d+)-(\w+).(\w+)$",
        "display_cover_image",
        name="cover-image"),
    url(r"^save$", "save", name="catalog-save"),
    url(r"^search$", "search", name="catalog-search"),
)


