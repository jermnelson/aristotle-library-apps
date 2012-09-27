"""
 mod:`app_settings` Fedora Batch App Settings
"""
import sys,os
import aristotle.settings as settings
print(os.path.join(settings.PROJECT_HOME,"aristotle/lib/"))
sys.path.append(os.path.join(settings.PROJECT_HOME,"aristotle/lib/"))

from fcrepo.http.restapi import FCRepoRestAPI
try:
    from aristotle.settings import FEDORA_URL,FEDORA_USERNAME,FEDORA_PASSWORD,FEDORA_NAMESPACE
except:
    FEDORA_URL = 'http://127.0.0.1/fedora/'
    FEDORA_USERNAME = 'fedoraAdmin'
    FEDORA_PASSWORD = 'fedora'
    FEDORA_NAMESPACE = 'fedora'
    

APP = {'current_view': {'title':'Fedora Batch'},
       'description': 'The Fedora Batch App provides a batch utilties for a Fedora Commons Repository',
       'icon_url':'fedora-commons.png',
       'productivity':True,
       'url':'fedora_batch/'}

fedora_repo = FCRepoRestAPI(repository_url=FEDORA_URL,
                            namespace= FEDORA_NAMESPACE,
                            username=FEDORA_USERNAME,
                            password=FEDORA_PASSWORD)
                            




