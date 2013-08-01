"""Module provides specific filters to support John Peabody Harrington Papers
Collection
"""
__author__ = "Jeremy Nelson"

from django import template
from django.utils.safestring import mark_safe
from bibframe.models import Instance
from aristotle.settings import REDIS_DATASTORE
register = template.Library()

@register.filter(is_safe=True)
def display_collection(placeholder):
    output = ""
    for i in range(1, int(REDIS_DATASTORE.get('global bf:Manuscript'))):
        work_key = 'bf:Manuscript:{0}'.format(i)
        title_key = REDIS_DATASTORE.hget(work_key, 'title')
        instance_key = REDIS_DATASTORE.hget(work_key, 'hasInstance')
        title = REDIS_DATASTORE.hget(title_key, 'titleValue')
        pdf_location = REDIS_DATASTORE.hget(instance_key,
                                            'schema:contentUrl')
        output += """<li><a href="/apps/discovery/Manuscript/{0}">{1}</a>
<a href="{2}"><i class="icon-download-alt"></i></a></li>
""".format(i, title, pdf_location)
    return mark_safe(output)

@register.filter(is_safe=True)
def display_topic_cloud(placeholder):
    topics = []
    for i in range(1, int(REDIS_DATASTORE.get('global bf:Topic'))):
        topic_key = 'bf:Topic:{0}'.format(i)
        topic_works_key = '{0}:works'.format(topic_key)
        total_works = int(REDIS_DATASTORE.scard(topic_works_key))
        if total_works < 3:
            topic_size = 12
        elif total_works < 10:
            topic_size = 16
        else:
            topic_size = total_works
        topics.append("""<a style="font-size: {0}px"
href="/apps/discovery/Topic/{1}">{2}</a>""".format(
    topic_size,
    i,
    REDIS_DATASTORE.hget(topic_key, 'label')))
    return mark_safe(", ".join(topics))
                          
    
@register.filter(is_safe=True)
def get_pdf_uri(creative_work):
    return mark_safe(REDIS_DATASTORE.hget(creative_work.hasInstance,
                                          'schema:contentUrl'))

@register.filter(is_safe=True)
def get_subjects(creative_work):
    work_key = creative_work.redis_key
    output = ""
    subject_work_key = "{0}:subject".format(work_key)
    if REDIS_DATASTORE.exists(subject_work_key):
        for topic_key in REDIS_DATASTORE.smembers(
            subject_work_key):
            topic_id = 'bf:Topic:{0}'.format(topic_key.split(":")[-1])
            label = REDIS_DATASTORE.hget(topic_id, 'label')
            output += """<li><a href="/apps/discovery/Topic/{0}">{1}</a>
            </li>
""".format(topic_id, label)
    else:
        topic_key = REDIS_DATASTORE.hget(work_key, 'subject')
        topic_id = topic_key.split(":")[-1]
        label = REDIS_DATASTORE.hget(topic_key, 'label')
        output += """<li><a href="/apps/discovery/Topic/{0}">{1}</a></li>
""".format(topic_id, label)
    return mark_safe(output)

