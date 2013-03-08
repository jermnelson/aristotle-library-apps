__author__ = "Jeremy Nelson"

import json, redis, os, csv
from bibframe.models import Instance, Holding, Work, TopicalConcept
from aristotle.settings import ANNOTATION_REDIS, AUTHORITY_REDIS, INSTANCE_REDIS, CREATIVE_WORK_REDIS, PROJECT_HOME

alt_titles = json.load(open(os.path.join(PROJECT_HOME,
                                         'dbfinder',
                                         'fixures',
                                         'alt-titles.json'),'rb'))
databases = json.load(open(os.path.join(PROJECT_HOME,
                                        'dbfinder',
                                        'fixures',
                                        'databases.json'),'rb'))
subjects = json.load(open(os.path.join(PROJECT_HOME,
                                       'dbfinder',
                                       'fixures',
                                       'subjects.json'),'rb'))

temp_bibframe = redis.StrictRedis()

# Redis Keys
base_key = 'dbfinder'
subject_hash_key  = "{0}:subjects".format(base_key)

def __get_database__(work_key,
                     instance_ds=INSTANCE_REDIS,
                     work_ds=CREATIVE_WORK_REDIS):
    """
    Helper function takes a work_key and an Instance datastore
    and Creative Work datastore and return a dict with the 
    title and uri
    
    :param work_key: Redis key of the Creative Work
    :param instance_ds: Instance Datastore, defaults to INSTANCE_REDIS
    :param work_ds: Creative Work Datastore, defaults to CREATIVE_WORK_REDIS
    """
    database = {'description': work_ds.hget(work_key,'description'),
                'title': work_ds.hget("{0}:title".format(work_key),
                                      'rda:preferredTitleForTheWork'),
                'varientTitle':list(work_ds.smembers('{0}:varientTitle'.format(work_key))),
                'uri':None,
                'work_key':work_key}
    instance_keys = work_ds.smembers("{0}:bibframe:Instances".format(work_key))
    for redis_key in instance_keys:
        if database['uri'] is None and instance_ds.hexists(redis_key,"uri"):
            database['uri'] = instance_ds.hget(redis_key,"uri")
    return database      

def get_databases(letter=None,
                  subject=None,
                  authority_ds=AUTHORITY_REDIS,
                  instance_ds=INSTANCE_REDIS,
                  work_ds=CREATIVE_WORK_REDIS):
    """
    Helper function takes either a letter or subject and returns 
    a sorted list of databases.

    :param letter: First character of database title
    :param subject: Subject
    """
    databases = []
    if letter is None and subject is None:
        raise ValueError("get_database error letter and subject are both None")
    if letter is not None and subject is not None:
        raise ValueError( "get_database error letter and subject cannot both have values")
    if letter is not None:
        alpha_key = "dbfinder:alpha:{0}".format(letter.upper())
        for work_key in authority_ds.smembers(alpha_key):
            databases.append(__get_database__(work_key,instance_ds,work_ds))
    if subject is not None:
        subject_key = "dbfinder:subject:{0}".format(subject)
        for work_key in authority_ds.smembers(subject_key):
            databases.append(__get_database__(work_key,instance_ds,work_ds))
    return sorted(databases, key=lambda x: x.get('title').lower())

def get_dbs_alpha(authority_ds=AUTHORITY_REDIS,
                  instance_ds=INSTANCE_REDIS,
                  work_ds=CREATIVE_WORK_REDIS):
    """
    Helper function returns a list of databases organized by the first character
    of the title
    """
    databases = []
    alpha_keys = authority_ds.sort("dbfinder:alphas",alpha=True)
    for key in alpha_keys:
        databases.append({'letter':key.split(":")[-1]})
    return databases
    
def get_dbs_subjects(authority_ds=AUTHORITY_REDIS,
                    instance_ds=INSTANCE_REDIS,
                    work_ds=CREATIVE_WORK_REDIS):
    """
    Helper function returns a list of databases organized by the first character
    of the title
    """
    databases = []
    subject_keys = authority_ds.sort("dbfinder:subjects",
                                     alpha=True)
    for key in subject_keys:
        label = authority_ds.hget(key,"label")
        databases.append({"subject":label})
    return sorted(databases, key=lambda x: x.get('subject'))

def load_databases_csv(csv_file=open(os.path.join(PROJECT_HOME,
                                                  'dbfinder',
                                                  'fixures',
                                                  'ccweb.csv')),
                       authority_ds=AUTHORITY_REDIS,
                       instance_ds=INSTANCE_REDIS,
                       work_ds=CREATIVE_WORK_REDIS):
    """
    Helper function updates the BIBFRAME Annotation and Instance
    datastores based on values from CSV file exported from
    legacy ILS

    :param csv_file_location: Defaults to ccweb.csv located in dbfinder
                              fixures directory.
    """
    for row in csv.DictReader(csv_file, delimiter="\t"):
        bib_number = row.get('RECORD #(BIBLIO)')[:-1] # Drop-off last char
        if instance_ds.hexists("ils-bib-numbers", bib_number):
            instance_key = instance_ds.hget("ils-bib-numbers", bib_number)
        else:
            raise ValueError("load_databases_csv bib number {0} not found".format(bib_number))
        work_key = instance_ds.hget(instance_key,
                                    'instanceOf')
        if len(row.get('246')) > 0:
            titles = [title.replace('"','') for title in row.get("246").split("|")]
            if len(titles) == 1:
                work_ds.hset(work_key, 'variantTitle', title[0])
            else:
                if work_ds.hexists(work_key, 'variantTitle'):
                    existing_variant_title = work_ds.hget(work_key,
                                                          'variantTitle')
                    if titles.count(existing_variant_title) < 0:
                        titles.append(existing_variant_title)
                    work_ds.hdel(work_key,'variantTitle')
                work_variant_title_key = "{0}:variantTitle".format(work_key)
                for title in raw_titles:
                    work_ds.sadd(work_variant_title_key,
                                 title)
        if len(row.get('590',[])) > 0:
            work_ds.hset(work_key, 'description', row.get('590'))
        if len(row.get('690', [])) > 0:
            subjects = row.get('690',[]).split("|")
            for raw_subject in subjects:
                name = raw_subject.replace('"', '')
                subject_key = "dbfinder:subject:{0}".format(name)
                if authority_ds.exists(subject_key):
                    if not authority_ds.sismember(subject_key,
                                                  work_key):
                        authority_ds.sadd(subject_key, work_key)
                else: # Assume this subject doesn't exist in the datastore
                    new_topic = TopicalConcept(primary_redis=authority_ds,
                                               description="Topic Used for Database-by-Subject view in dbfinder",
                                               label=name)
                    setattr(new_topic, "bibframe:Works", work_key)
                    setattr(new_topic, "prov:PrimarySource", "local")
                    new_topic.save()
                    work_ds.sadd("{0}:subject".format(work_key),
                                 new_topic.redis_key)
                    authority_ds.sadd(subject_key, work_key)
        

    

def legacy_load_databases_json():
    subject_dict = {}
    alt_title_dict = {}
    for row in subjects:
        subject_dict[row['pk']] = {"name":row['fields']['name']}
        new_topic = TopicalConcept(primary_redis=AUTHORITY_REDIS,
                                   description="Topic Used for Database-by-Subject view in dbfinder",
                                   label=row['fields']['name'])
        new_topic.save()
        subject_dict[row['pk']]["redis_key"] = new_topic.redis_key
        AUTHORITY_REDIS.sadd("dbfinder:subjects",new_topic.redis_key) 
    for row in alt_titles:
        db_key = row['fields']['database']
        if alt_title_dict.has_key(db_key):
            alt_title_dict[db_key].append(row['fields']['title'])
        else:
            alt_title_dict[db_key] = [row['fields']['title'],]
    for i,row in enumerate(databases):
        db_pk = row['pk']
        description = row['fields']['description']
        title = row['fields']['title']
        new_work = Work(primary_redis=CREATIVE_WORK_REDIS,
                        description=description,
                        title={'rda:preferredTitleForTheWork':title})
        if alt_title_dict.has_key(db_pk):
            new_work.varientTitle = []
            for alt_title in alt_title_dict[db_pk]:
                new_work.varientTitle.append(alt_title)
            new_work.varientTitle = set(new_work.varientTitle)
        new_work.save()
        subject_keys = []
        for subject_id in row['fields']['subjects']:
           subject_name = subject_dict[subject_id].get("name",None)
           if subject_name is not None:
               subject_keys.append(subject_dict[subject_id].get("redis_key"))
               AUTHORITY_REDIS.sadd("dbfinder:subject:{0}".format(subject_name),
                                    new_work.redis_key)
        if len(subject_keys) > 0:
            new_work.subject = set(subject_keys)
        new_work.save()
        alpha_redis_key = "dbfinder:alpha:{0}".format(title[0].upper())
        AUTHORITY_REDIS.sadd(alpha_redis_key,
                             new_work.redis_key)
        AUTHORITY_REDIS.sadd("dbfinder:alphas",alpha_redis_key)
        new_instance = Instance(primary_redis=INSTANCE_REDIS,
                                instanceOf=new_work.redis_key,
                                uri=row['fields']['url'])
        new_instance.save()
        CREATIVE_WORK_REDIS.sadd("{0}:bibframe:Instances".format(new_work.redis_key),
                                 new_instance.redis_key)
        print("Added {0}".format(title))
