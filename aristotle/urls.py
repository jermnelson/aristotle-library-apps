"""
 :mod:`urls` Url routing for the Aristotle Library Apps Project

 Most basic configuration is to provide django.conf.urls for all of your active apps located
 in your local_settings.py file.
"""
__author__ = "Jeremy Nelson"

import os
from aristotle.settings import ACTIVE_APPS, PROJECT_HOME
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib.auth.views import login, logout
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
##    url(r'^$', 'discovery.views.app', name='home'),
    url(r'^$', 'portfolio.views.default', name='home'),
##    url(r'^$','portfolio.views.default', name='portfolio.home'),
    url(r'^feedback', 'aristotle.views.feedback'),
    url(r'^background.html$','aristotle.views.background', name='background'),
    url(r'^getting-started.html$','aristotle.views.starting', name='getting-started'),
    url(r'^apps/accounts/login[$|/]', login),
    url(r'^apps/accounts/logout[$|/]', 'aristotle.views.app_logout', name='logout'),
    url(r'^apps/app_login[$|/]', 'aristotle.views.app_login', name='app-login'),
    url(r'^apps/website-footer$', 'aristotle.views.website_footer'),
    url(r'^apps/website-header$', 'aristotle.views.website_header'),
    url(r'^accounts/login[$|/]', login),
    url(r'^accounts/logout[$|/]', 'aristotle.views.app_logout', name='logout'),
##    url(r'^apps/discovery[$|/]', include('discovery.urls')),
##    url(r'^apps/bibframe[$|/]', include('bibframe.urls')),
##    url(r'^apps/call_number/', include('call_number.urls')),
##    url(r'^apps/dbfinder/', include('dbfinder.urls')),
##    url(r'^etd/', include('etd.urls')),
##    url(r'^etd[$|/]', include('ccetd.urls')),
##    url(r'^apps/fedora_utilities/', include('fedora_utilities.urls')),
##    url(r'^apps/hours/', include('hours.urls')),
##    url(r'^apps/[m|M][a|A][r|R][c|C][r|R]/', include('marcr.urls')),
##    url(r'^apps/marc_batch/', include('marc_batch.urls')),
##    url(r'^apps/orders/', include('orders.urls')),
##    url(r'^apps/person_authority/', include('person_authority.urls')),
##    url(r'^apps/portfolio/', include('portfolio.urls')),
##    url(r'^apps/RDA[c|C]ore/', include('RDACore.urls')),
##    url(r'^apps/reserve_search/', include('reserve_search.urls')),
##    url(r'^apps/title_search/', include('title_search.urls')),
##    url(r'^apps/','portfolio.views.default', name='portfolio.home'),




)

# Uncomment the admin/doc line below to enable admin documentation:
urlpatterns.append(url(r'^admin/doc/',
                       include('django.contrib.admindocs.urls')))

# Uncomment the next line to enable the admin:
urlpatterns.append(url(r'^admin/',
                       include(admin.site.urls)))
urlpatterns.append(url(r'^captcha/',
                       include('captcha.urls')))

for app in ACTIVE_APPS:
    if app == 'ccetd':
        urlpatterns.append(
            url(r'^apps/etd[$|/]',
                include('ccetd.urls')))
    else:
        if os.path.exists(os.path.join(PROJECT_HOME,
                                    app,
                                   'urls.py')):
            urlpatterns.append(
                url(r'^apps/{0}[$|/]'.format(app),
                include('{0}.urls'.format(app))))



