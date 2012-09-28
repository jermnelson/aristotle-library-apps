from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib.auth.views import login, logout
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'aristotle.views.default', name='home'),
    url(r'^background.html$','aristotle.views.background',name='background'),
    url(r'^getting-started.html$','aristotle.views.starting',name='getting-started'),
    url(r'^accounts/login/$', login),
    url(r'^accounts/login/$', logout),
    url(r'^apps/article_search/', include('article_search.urls')),
    url(r'^apps/book_search/', include('book_search.urls')),
    url(r'^apps/call_number/', include('call_number.urls')),
    url(r'^apps/dbfinder/', include('dbfinder.urls')),
##    url(r'^apps/fedora_batch','fedora_batch.views.default'),
    url(r'^apps/fedora_batch/home.html','fedora_batch.views.default'),
    url(r'^apps/hours/', include('hours.urls')),
    url(r'^apps/marc_batch/', include('marc_batch.urls')),
    url(r'^apps/orders/', include('orders.urls')),
    url(r'^apps/portfolio/', include('portfolio.urls')),
    url(r'^apps/RDA[c|C]ore/', include('RDACore.urls')),
    url(r'^apps/reserve_search/', include('reserve_search.urls')),
    url(r'^apps/title_search/', include('title_search.urls')),
    url(r'^apps/','portfolio.views.default', name='portfolio.home'),
    
                       
                       
    # url(r'^aristotle/', include('aristotle.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
