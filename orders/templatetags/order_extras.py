"""
 :mod:`orders_extra` Order App Template Filters including a HTMLCalendar
"""
from datetime import datetime,timedelta
from calendar import HTMLCalendar
from django.template import Context,Library,loader
from django.utils import simplejson as json
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup

register = Library()

def create_nav_btn(soup,date,text):
    """
    Helper functions for month_calendar, generates a navigation button
    for calendar

    :param soup: BeautifulSoup parser of document
    :param date: Date to create nav button
    :param text: Text for button
    """
    nav_th = soup.new_tag('th',attrs=[('colspan','2')])
    nav_th['class'] = 'month'
    nav_a = soup.new_tag('a',href='/apps/orders/%s/%s' % (date.year,
                                                          date.month))
    nav_a.string = text
    if date > datetime.today():
        nav_a['class'] = "btn btn-mini btn-info disabled"
        nav_a['href'] = '#'
    else:
        nav_a['class'] = "btn btn-mini btn-info"
    nav_th.insert(0,nav_a)
    return nav_th
    

def month_calendar(date=datetime.today()):
    """
    Filter displays a HTML calendar for inclusion in templates with
    links to existing transactions in the datastore

    :param date: Date to display Monthly calendar, default is the
                 current month
    """
    raw_month_html = HTMLCalendar().formatmonth(date.year,date.month)
    month_soup = BeautifulSoup(raw_month_html)
    
    time_delta = timedelta(days=31)
    # Creates Previous and Next month (if date isn't current)
    first_row = month_soup.find('tr')
    exist_th = first_row.find('th')
    exist_th['colspan'] = 3    
    previous_month = date - time_delta
    next_month = date + time_delta
    create_nav_btn(month_soup,previous_month,"&laquo;")
    create_nav_btn(month_soup,next_month,"&raquo;")
    pretty_html = month_soup.prettify()
    print(type(pretty_html))
    return mark_safe(pretty_html)
    

register.filter('month_calendar',month_calendar)
