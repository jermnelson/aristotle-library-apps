__author__ = "Jeremy Nelson"
import json, os
from django.db import models

from aristotle.settings import PROJECT_HOME
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS, CREATIVE_WORK_REDIS, INSTANCE_REDIS

SCHEMA_RDFS = json.load(open(os.path.join(PROJECT_HOME,
                                          'schema_org',
                                          'fixures',
                                          'all.json'),
                             'rb'))

