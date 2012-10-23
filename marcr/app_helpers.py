"""
 :mod:`app_helpers` - Redis and other helper classes for the Bibliographic
 Framework App
"""
__author__ = "Jeremy Nelson"


def get_brief(**kwargs):
    """
    Searches datastore and returns brief record from marcr:Work,
    marcr:Instance, and marcr:Authority datastores

    :param redis_work: Redis marcr:Work datastore
    :param redis_instance: Redis marcr:Instance datastore
    :param redis_authority; Redis marcr:Authority datastore
    :param work_key: Redis marcr:Work key
    :param instance_key: Redis marcr:Instance key
    """
    output,work_key,instance_keys = {},None,[]
    redis_authority = kwargs.get('redis_authority')
    redis_instance = kwargs.get('redis_instance')
    redis_work = kwargs.get('redis_work')
    if kwargs.has_key('work_key'):
        work_key = kwargs.get('work_key')
    if kwargs.has_key('instance_key'):
        instance_keys.append(kwargs.get('instance_key'))
        if work_key is None:
            work_key = redis_instance.hget(instance_keys[0],'marcr:Work')
            
        for instance_key in instance_keys:
            if redis_instance.hget(instance_key,'marcr:Work') != work_key:
                return {"result":"error",
                           "msg":"{0} is not assocated as a work with {1}".format(work_key,
                                                                                  instance_key)}
            work_key = redis_instance.hget(instance_key,'marcr:Work')
    else:
        instance_keys = redis_work.smembers("{0}:marcr:Instances".format(work_key))
    output["title"] = unicode(redis_work.hget("{0}:rda:Title".format(work_key),
                                              "rda:preferredTitleForTheWork"),
                              errors="ignore")
    output['ils-bib-numbers'] = []
    for instance_key in instance_keys:
        output['ils-bib-numbers'].append(redis_instance.hget("{0}:rda:identifierForTheManifestation".format(instance_key),
                                                             'ils-bib-number'))
    output['creators'] = []
    creator_keys = redis_work.smembers("{0}:rda:creator".format(work_key))
    for creator_key in creator_keys:
        output['creators'].append(unicode(redis_authority.hget(creator_key,
                                                               "rda:preferredNameForThePerson"),
                                          errors="ignore"))
    return output

