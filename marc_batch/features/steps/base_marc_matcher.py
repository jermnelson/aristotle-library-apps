"""
 :mod:`base_marc_matcher` Common matching steps for MARC batch jobs
"""
__author__ = "Jeremy Nelson"

from behave import *
import pymarc
import nose

@given("we have a MARC record")
def marc_exists(context):
    """
    Asserts that a MARC record exists in the context

    :param context: Context for MARC record
    """
    assert context.marc_record

@when('the "<code>" field position "<position>" is "<value>"')
def check_field_position_value(context,
                               code,
                               position,
                               value):
    """
    Checks that a MARC field and position are equal to a passed
    in value.

    :param context: Context
    :param code: MARC Field code
    :param position: Position of value, 0-index
    :param value: value of field
    """
    # Hack to get around different uses of the | character in Gherkin
    # verses MARC
    if value == 'PIPE':
        value = '|'
    elif value == 'None':
        value = None
    marc_fields = context.marc_record.get_fields(code)
    nose.tools.assert_greater(marc_fields,0)
    for field in marc_fields:
        extracted_value = field.data[position]
        nose.tools.eq_(extracted_value,
                       value)
        
@when('the "{code}" field subfield "{subfield}" is "{value}"')
def check_field_subfield_value(context,
                               code,
                               subfield,
                               value):
    """
    Check that a MARC field and subfield are equal to a
    value.

    :param context: Context
    :param code: MARC Field code
    :param subfield: MARC subfield, if numeric and code < 050, assume
                     value is the position
    :param value: value of subfield
    """
    marc_fields = context.marc_record.get_fields(code)
    nose.tools.assert_greater(marc_fields,0)
    for field in marc_fields:
        subfields = field.get_subfields(subfield)
        nose.tools.assert_in(value,subfields)

@when('"{code}" subfield "{subfield}" has "{snippet}"')
def check_and_store_subfield_snippet(context,
                                     code,
                                     subfield,
                                     snippet):
    """
    Checks and stores a subfield snippet in context

    :param context: Context
    :param code: Field code
    :param subfield: MARC subfield, if numeric and code < 050, assume
                     value is the position
    """
    context.snippet = snippet

@when('any "{code}" value is "{value}"')
def check_for_value_in_subfields(context,
                                 code,
                                 value):
    """
    Checks for any value in MARC field's subfields

    :param context: Context
    :param code: MARC Field code
    :param subfield: MARC subfield, if numeric and code < 050, assume
                     value is the position
    """
    field_value = context.marc_record[code]
    

@then('the "{code}" subfield "{subfield}" ends with "{value}"')
def update_and_check_ends_with(context,
                               code,
                               subfield,
                               value):
    """
    Replaces and checks that end of the subfield is the value

    :param context: Context
    :param code: Field code
    :param subfield: MARC subfield
    :param value: value of the last chars in the subfield's value
    """
    marc_fields = context.marc_record.get_fields(code)
    for field in marc_fields:
        nose.tools.assert_false(field.is_control_field())
        subfields = field.get_subfield(subfield)
        for subfield_value in subfields:
            if not subfield_value.endswith(value):
                subfield_value += value
                subfields.remove(value)
                field.add_subfield(subfield,subfield_value)
            
@then('any "<code>" value of "<value>" is replaced by "<replacement>"')
def update_any_occurances_of_char(context,
                                  code,
                                  value,
                                  replacement):
    marc_fields = context.marc_record.get_fields(code)
    for field in marc_fields:
        if field.is_control_field():
            field.data = field.data.replace(value,replacement)

@then('the "{code}" subfield "{subfield}" snippet is now "{value}"')
def update_subfield_snippet(context,
                            code,
                            subfield,
                            value):
    """
    Replaces a new value in a subfield snippet for a MARC field

    :param context: Context
    :param code: Field code
    :param subfield: MARC subfield, if numeric and code < 050, assume
                     value is the position
    :param value: value of subfield
    """
    if context.snippet is None:
        return None
    marc_fields = context.marc_record.get_fields(code)
    for field in marc_fields:
        if field.is_control_field():
            position = subfield
            old_value = list(field.value())
            old_value[int(position)] = value
            field.value = old_value
        else:
            subfield_value = field.delete_subfield(subfield)
            new_value = subfield_value.replace(context.snippet,
                                               value)
            field.add_subfield(subfield,new_value)
       
 
