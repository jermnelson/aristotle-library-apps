__author__ = "Jeremy Nelson"

import json
import os
import re

from aristotle.settings import PROJECT_HOME
##from pyparsing import alphas, nums, dblQuotedString, Combine, Word, Group, delimitedList, Suppress, removeQuotes
##
##
##bibframeMARCMap = None
##def getbibframeMARCMap():
##    global bibframeMARCMap
##
##    if bibframeMARCMap is None:        
##        tag = Word( nums, min=3, max=3 )
##        subfields = delimitedList(Word("$", alphas), "+")
##        subfield_conditional = Word( "/", alphas ) | Word(",", alphas)
##        field_range = nums + "XX"
##
##
##test_maps = {'manufacture': '260 $e+$f+$g',
##             'subject': '6XX, 043',
##             'title': '245 $a',
##             'upi': '0247-+2"uri"/a,z'}



    
BASIC_CONDITIONAL_RE = re.compile(r"""
if\s(?P<marc>marc:\w+)
\s(?P<operator>\D+)\s
'(?P<string>\w+)'
""",
                            re.VERBOSE)
METHOD_CONDITIONAL_RE = re.compile(r"""
if\s(?P<marc>marc:\w+)
[.]+(?P<method>\w+)\('(?P<param>\w+)'\)
\s(?P<operator>[>|<|=]+)\s
(?P<string>\w+)
""",
                                  re.VERBOSE)

MARC_FLD_RE = re.compile(r"""
[marc:]                   # Matches M or underscore
(?P<tag>\d{1,3}        # Matches specific MARC tags
  | X{2,2})
(?P<ind1>\w{1,1})       # Matches indicator 1
(?P<ind2>\w{1,1})       # Matches indicator 2
(?P<subfield>\w{1,1})  # Matches subfield
""",
                         re.VERBOSE)


class MARCParser(object):

    def __init__(self, **kwargs):
        self.entity_info = {}
        self.record = kwargs.get('record')
        self.rules = json.load(
            open(os.path.join(PROJECT_HOME,
                              'bibframe',
                              'ingesters',
                              kwargs.get('rules_filename')),
                 'rb'))

    def parse(self):
        """Method parses through rules and applies conditional, retriving,
        and post-processing for each in rules.
        """
        for property_name, rule in self.rules.iteritems():
            self.entity_info[property_name] = []
            marc_rules = rule.get('marc')
            if not marc_rules:
                continue
            for marc_rule in rule.get('marc'):
                marc_value = None
                if marc_rule.get('conditional', None):
                    result = conditional_MARC21(
                        self.record,
                        marc_rule)
                    if len(result) > 0:
                        marc_value = result
                else:
                    mapping = marc_rule.get('map')
                    if mapping is not None:
                        for marc_pattern in mapping:
                            result = parse_MARC21(
                                self.record,
                                marc_pattern)
                            if len(result) > 0:
                                marc_value = result
                if marc_value is not None:
                    self.entity_info[property_name].extend(marc_value)
            if marc_rule.get('post-processing', None):
                self.entity_info[property_name] = post_processing(
                    self.entity_info[property_name],
                    marc_rule.get('post-processing'))
            

                
                    
        

def conditional_MARC21(record, rule):
    """Function takes a conditional and a mapping dict (called a rule)
    and returns the result if the test condition matches the antecedient
    
    Parameters:
    record -- MARC21 record
    rule -- Rule to match MARC field on
    """
    output = []
    if rule.has_key('conditional'):
        conditional = BASIC_CONDITIONAL_RE.search(
            rule.get('conditional'))
        if conditional is None:
            conditional = METHOD_CONDITIONAL_RE.search(
                rule.get('conditional'))
        condition_result = conditional.groupdict()
        operator = condition_result.get('operator')
        condition_marc_search = MARC_FLD_RE.search(
            condition_result.get('marc'))
        condition_marc_result = condition_marc_search.groupdict()
        for mapping in rule.get('map'):
            search = MARC_FLD_RE.search(mapping)
            if not search:
                continue
            result = search.groupdict()
            fields = record.get_fields(result.get('tag'))
            if len(fields) < 1:
                return output
            for field in fields:
                if ['is', '='].count(operator) > 0:
                    if parse_variable_field(
                        field,
                        condition_marc_result) is [condition_result.get('string')]:
                        output.extend(
                            parse_variable_field(field, result))

##        if condition_result.has_key('method'):
##            for value in marc_values:
##                method_value = getattr(value,
##                                       condition_result.get('method'))(
##                                           condition_result.get('param'))
##                value = method_value

##        
##        if len(marc_values) > 0:
##        for row in marc_values:
##            if ['is', '='].count(operator) > 0:
##                if unicode(row) == condition_result.get('string'):
##                        __apply_map__(rule.get('map'))
##                elif operator == '>':
##                    if row > condition_result.get('string'):
##                        __apply_map__(rule.get('map'))
##                elif operator == '<':
##                    if row < condition_result.get('string'):
##                        __apply_map__(rule.get('map'))
    print(output)
    return output

def parse_variable_field(field, re_dict):
    """Function takes a MARC21 field and the Regex dictgroup and
    return a list of the subfields that match the Regex patterns.

    Parameters:
    field -- MARC21 field
    re_dict -- Regular Expression dictgroup
    """
    output = []
    if field is None or re_dict is None:
        return output
    test_ind1 = re_dict.get('ind1').replace("_", " ")
    test_ind2 = re_dict.get('ind2').replace("_", " ")
    if field.indicators == [test_ind1, test_ind2]:
        output = field.get_subfields(re_dict.get('subfield'))
    return output

def parse_MARC21(record, mapping):
    """Function returns a list of values from a MARC record that match
    a MARC 21 mapping in the format marc:XXXiiY where XXX is the tag, ii is
    indicator1 and indicator2, and Y is the subfield.

    Parameters:
    record -- MARC21 record
    mapping -- Rule to match MARC field on
    """
    output = []
    search = MARC_FLD_RE.search(mapping)
    if not search:
        return output
    regex_result = search.groupdict()
    fields = record.get_fields(regex_result.get('tag'))
    for field in fields:
        if hasattr(field, 'indicators'):
            var_fld_result = parse_variable_field(field,
                                                  regex_result)
            if len(var_fld_result) > 0:
                output.extend(var_fld_result)
    return output
    
def post_processing(result, directive):
    """Performs one or more opeations on the result of MARC21-to-BIBFRAME
    mapping.

    Parameters:
    result -- result of parsing the MARC with BIBFRAME rule
    directive -- Instructions for manipulating the result
    """
    # Combines all of results into a single string
    if directive == 'concat':
        return ''.join(result)
    elif type(directive) == dict:
        if directive.get('type') == 'delimiter':
            return '{0}'.format(directive.get('value')).join(result)
