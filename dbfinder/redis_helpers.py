__author__ = "Jeremy Nelson"

import json, redis
from bibframe.models import Instance, Holding, Work, TopicalConcept
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS, INSTANCE_REDIS, CREATIVE_WORK_REDIS

alt_titles = json.load(open('fixures/alt-titles.json','rb'))
databases = json.load(open('fixures/databases.json','rb'))
subjects = json.load(open('fixures/subjects.json','rb'))

temp_bibframe = redis.StrictRedis()

# Redis Keys
base_key = 'dbfinder'
subject_hash_key  = "{0}:subjects".format(base_key)

def load_databases():
    subject_dict = {}
    alt_title_dict = {}
    for row in subjects:
        subject_dict[row['pk']] = row['fields']['name']
        new_topic = TopicalConcept(primary_redis=AUTHORITY_REDIS,
                                   description="Topic Used for Database-by-Subject view in dbfinder",
                                   label=row['fields']['name'])
        new_topic.save()  
    for row in alt_titles:
        db_key = row['fields']['database']
        if alt_title_dict.has_key(db_key):
            alt_title_dict[db_key].append(row['fields']['title'])
        else:
            alt_title_dict[db_key] = [row['fields']['title'],]
    for row in databases:
        db_pk = row['pk']
        description = row['fields']['description']
        title = row['fields']['title']
        new_work = Work(primary_redis=WORK_REDIS,
                        description=description,
                        title={'rda:preferredTitleOfWork':title})
        if alt_title_dict.has_key(db_pk):
            new_work.varientTitle = []
            for title in alt_title_dict[db_pk]:
                new_work.varientTitle.append(title)
        new_work.save()
        new_instance = Instance(primary_redis=INSTANCE_REDIS,
                                instanceOf=new_work.redis_id,
                                uri=row['url'])
        new_instance.save()
        
          
