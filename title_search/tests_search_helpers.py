"""
 :mod:`test_search_helpers` Unit tests for the search helpers module
"""
__author__ = "Jeremy Nelson"

import search_helpers


def check_process_title(raw_title,expected_title):
    func_value = search_helpers.process_title(raw_title)
    assert func_value == expected_title

def test_process_title():
    for raw_title in [('','')]:
        yield check_process_title,raw_title[0],raw_title[1]

        
