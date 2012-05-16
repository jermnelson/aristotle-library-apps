"""
 :mod:`` YBP specific MARC transformations for EBL ebooks in Alliance
 program
"""
__author__ = "Jeremy Nelson"
from behave import *
import nose

@when('the 050 has a second subfield a')
def second_050_subfield_a(context):
    """
    Method checks to see any of the 050 MARC fields has a second
    subfield a.

    :param context: Context
    """
    all_050_fields = context.marc_record.get_fields('050')
    for field in all_050_fields:
        all_a_subfields = field.get_subfields('a')
        nose.tools.assert_greater(all_a_subfields,1)
               

@then('the 050 does not have a second subfield a')
def remove_second_050_subfield_a(context):
    """
    Method removes any additional subfield "a"s from
    record.

    :param context: Context
    """
    all_050_fields = context.marc_record.get_fields('050')
    for field in all_050_fields:
        first_a_value = field.delete_subfield('a')
        rest_a_subfields = field.get_subfields('a')
        for counter in range(0,len(rest_a_subfields)):
            field.delete_subfield('a')
        field.add_subfield('a',first_a_value)
        nose.tools.eq_(len(field.get_subfields('a')),1)


        
        

