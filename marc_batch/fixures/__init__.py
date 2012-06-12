"""
 :mod:`__init__` Loads help rst files for use in the marc_batch app
"""
__author__ = "Jeremy Nelson"

from docutils.core import publish_string
from bs4 import BeautifulSoup
import os,sys
import json
from aristotle.fixures import get_file

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
help_loader = dict()
json_loader = dict()

fixures_walker = os.walk(CURRENT_DIR)
fixures_listing = next(fixures_walker)[2]

for filename in fixures_listing:
    root,extension = os.path.splitext(filename)
    if extension == '.rst':
        if root.find("help") > -1:
            raw_contents = get_file(filename,CURRENT_DIR)
            rst_contents = publish_string(raw_contents,
                                          writer_name="html")
            rst_soup = BeautifulSoup(rst_contents)
            main_contents = rst_soup.find("div",attrs={"class":"document"})
            help_loader[root] = main_contents.prettify()
    elif extension == '.json':
        raw_contents = get_file(filename,CURRENT_DIR)
        json_loader[root] = json.loads(raw_contents)

