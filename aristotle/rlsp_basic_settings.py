import os
import redis
IS_CLUSTER = False
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_HOME = os.path.split(PROJECT_ROOT)[0]

ACTIVE_APPS = ['aristotle',
               'discovery',
               'fedora_utilities',
               'portfolio']

ACTIVE_TEMPLATE_DIRS = [
    os.path.join(PROJECT_HOME, 'ccetd/templates/'),
    os.path.join(PROJECT_HOME,'discovery/templates/discovery/'),
    os.path.join(PROJECT_HOME,'discovery/templates/discovery/snippets/'),
    os.path.join(PROJECT_HOME,'fedora_utilties/templates/fedora_utilties/'),
    os.path.join(PROJECT_HOME,'fedora_utilties/templates/fedora_utilties/snippets/'),
    os.path.join(PROJECT_HOME,'marc_batch/templates/marc_batch/'),
    os.path.join(PROJECT_HOME,'marc_batch/templates/marc_batch/snippets/'),
    os.path.join(PROJECT_HOME,'portfolio/templates/'),
    os.path.join(PROJECT_HOME,'portfolio/templates/portfolio/snippets/')]

ACTIVE_STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, 'assets'),
    os.path.join(PROJECT_HOME, 'article_search/assets'),
    os.path.join(PROJECT_HOME, 'bibframe/assets'),
    os.path.join(PROJECT_HOME, 'call_number/assets'),
    os.path.join(PROJECT_HOME, 'discovery/assets'),
    os.path.join(PROJECT_HOME, 'marc_batch/assets'),
    os.path.join(PROJECT_HOME, 'portfolio/assets'),
]


GOOGLE_API_KEY = None
LOCAL = True
PRODUCTION = False
SINGLE_SERVER = True
IS_CONSORTIUM = False
#! CHANGE this value
#! >> import hashlib, os
#! >> sha256_hash = hashlib.sha256(os.urandom(45))
#! >> sha256_hash.hexdigest()
SECRET_KEY = 'cf951757127064811df2312c5576c1bb6d61a53593d3992ef8f59058fbfe7111'
CUSTOM_AUTHENTICATION_BACKENDS = []
DISCOVERY_RECORD_URL = None
ILS_PATRON_URL = None
SOLR_URL = None
# INSTITUTION settings
INSTITUTION = {'background-logo': None,
               'name': 'Default Library',
               'logo': None,
               'links': [{'title': 'Home',
                          'url': "/"}],
               'url': None}
# REDIS Datastore Settings
REDIS_MASTER_PORT=6380
REDIS_MASTER_HOST = '127.0.0.1'
REDIS_DATASTORE = redis.StrictRedis(host=REDIS_MASTER_HOST,
                                    port=REDIS_MASTER_PORT)
# These need to be set to a FEDORA Commons server
FEDORA_URI = ''
FEDORA_ROOT = ''
FEDORA_USER = ''
FEDORA_PASSWORD = ''
FEDORA_MODEL = ''

FEATURED_INSTANCES = []

    
    

