"""
 :mod:`base_marc_matcher` Common matching steps for MARC batch jobs
"""
__author__ = "Jeremy Nelson"

from behave import *
import pymarc,copy
MARC_FILENAME = 'C:\\Users\\jernelson\\Development\\ybp-dda-for-ebl.mrc'
 

def before_all(context):
    """
    Function sets-up `base_marc_matcher` with MARC record

    :param context: behave context object
    """
    marc_reader = pymarc.MARCReader(open(MARC_FILENAME,'rb'))
    context.original_record = marc_reader.next()
    context.marc_record = copy.deepcopy(context.original_record)


def after_all(context):
    """
    Function saves modified MARC record to file system

    :param context: behave context object
    """
    marc_filename = open('modified-ybp-dda-for-ebl.mrc','wb')
    marc_filename.write(context.marc_record.as_marc())
    marc_filename.close()
    
    
