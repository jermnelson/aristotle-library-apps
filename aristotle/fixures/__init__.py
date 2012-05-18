"""
 mod:`__init__` This loads all RST and JSON files in the fixures directories
 and making the contents available for use within the Aristotle Library Apps
 project
"""
__author__ = "Jeremy Nelson"

import os,sys
import json

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
rst_loader = dict()
json_loader = dict()

fixures_walker = os.walk(CURRENT_DIR)
fixures_listing = next(fixures_walker)[2]

def get_file(filename):
    """
    Helper function opens and returns the file contents of filename

    :param filename: Filename
    """
    file_obj = open(os.path.join(CURRENT_DIR,filename),'rb')
    file_contents = file_obj.read()
    file_obj.close()
    return file_contents

for filename in fixures_listing:
    root,extension = os.path.splitext(filename)
    if extension == '.json':
        raw_contents = get_file(filename)
        json_loader[root] = json.loads(raw_contents)
    elif extension == '.rst':
        rst_loader[root] = get_file(filename)
        
