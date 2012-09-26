"""
 mod:`views` Fedora Batch App Views
"""
from app_settings import APP,fedora_repo
from aristotle.settings import INSTITUTION
from django.views.generic.simple import direct_to_template

def default(request):
    """
    Default view for `Fedora Batch App`_

    :param request: HTTP Request
    """
    return direct_to_template(request,
                              'fedora_batch/app.html',
                              {'app':APP,
                               'institution':INSTITUTION})
    
