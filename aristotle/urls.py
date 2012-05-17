from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'aristotle.views.default', name='home'),
    url(r'^apps/call_number/', include('call_number.urls')),
    url(r'^apps/hours/', include('hours.urls')),
    url(r'^apps/marc_batch/', include('marc_batch.urls')),
    url(r'^apps/orders/', include('orders.urls')),
    url(r'^apps/portfolio/', include('portfolio.urls')),
    url(r'^apps/','portfolio.views.default', name='portfolio.home'),
    
                       
                       
    # url(r'^aristotle/', include('aristotle.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
##    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
##    url(r'^admin/', include(admin.site.urls)),
)
