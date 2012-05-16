"""
 :mod:`nav_bar_steps` Lettuce Testing steps for the Library App Portfolio App
"""
__author__ = 'Jeremy Nelson'

from lettuce import *
from lxml import html
from django.test.client import Client
from nose.tools import assert_equals
from portfolio.app_settings import APP
import logging,sys

@before.all
def set_browser():
    """
    Creates a browser client for the lettuce test environment
    """
    world.browser = Client()
    world.app = APP

@step('I access the Portfolio App with a (\w+)')
def default_portfolio_app(step,section):
    """
    Extract the section from the default portfolio app view

    :param step: Step in the features test
    :param section: Specific app section
    """
    response = world.browser.get(world.app['url'])
    error_output = open('error.txt','a')
    error_output.write(response.content)
    error_output.write("\n\nNEXT %s\n" % world.browser.get('/').content)
    error_output.close()
    world.dom = html.fromstring(response.content)
    result_list = world.dom.xpath("//div[@class='row-fluid %s']" % section)
    if len(result_list) > 0:
        world.section = result_list[0]

@step('I see Portfolio App Navigation Action Bar')
def access_portfolio_app(step):
    """
    Tests the existence of a section in the Portfolio App

    :param step: Step in the features test
    """
    assert world.section is not None

@step('I see the (\w+) in the Navigation Action Bar\sis\b\s(.*)\b')
def test_exists_and_value(step,section_item_name,item_value=None):
    """
    Tests if the section item exists in the section, if a value of 
    the item is provided, attempts to extract value from the section 
    item

    :param section_item_name: Name of the item in a section
    :param item_value: Default is None, tests item's value with this value
    """
    item = world.section.xpath('div[@id="%s"]' % section_item_name)
    assert item is not None
    if item_value is not None:
        assert item.text is item_value

