"""
 :mod:`marc_batch_extras` General tags for Aristotle Library Apps MARC record
 batch upload
"""
__author__ = 'Jeremy Nelson'
import aristotle.settings as settings
from django.template import Context,Library,loader
from django.utils import simplejson as json
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup

register = Library()

def generate_job_item(job,current_job=None):
    """
    Calls and generates HTML snippet for a simple job as list item
    in the side navigation bark

    :job_listing: Row Job
    :current_job: Current job, can be none
    :rtype: Generated HTML or None
    """
    job_soup = BeautifulSoup()
    li = job_soup.new_tag("li")
    job_link = job_soup.new_tag("a",
                                href="/apps/marc_batch/jobs/{0}/".format(job.pk))
    job_link.string = job.name
    li.append(job_link)
    if current_job is not None:
        if job.pk == current_job.pk:
            li['class'] = 'active'
            job_tasks = job_soup.new_tag("ul")
            job_tasks["class"] = "nav nav-list"            
            history_li = job_soup.new_tag("li")
            history_link = job_soup.new_tag("a",
                                            href="/apps/marc_batch/jobs/{0}/history/".format(current_job.pk))
            history_link.string = "History"
            history_li.append(history_link)
            job_tasks.append(history_li)
            li.append(job_tasks)
            print(li)
    return mark_safe(str(li))

register.filter('generate_job_item',generate_job_item)
