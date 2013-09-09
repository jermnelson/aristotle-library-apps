__author__ = "Jeremy Nelson"

import json
import os
import re

from aristotle.settings import PROJECT_HOME, REDIS_DATASTORE
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


MARC_FIXED_CODES = {
    '007': json.load(
        open(os.path.join(
            PROJECT_HOME,
            'marc_batch',
            'fixures',
            'marc-007-codes.json'))),
    'lang': json.load(
        open(os.path.join(
            PROJECT_HOME,
            'marc_batch',
            'fixures',
            'marc-language-code-list.json')))}

    
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

MARC_FX_FLD_RE = re.compile(r"""
[marc:]                   # Matches M or underscore
(?P<tag>\d{3,3})        # Matches specific MARC tags
(?P<code>\w{1,1})     # Code value in fixed position
(?P<position>\d{2,2})  # Postition in fixed field
""",
                            re.VERBOSE)

MARC_FX_FLD_RANGE_RE = re.compile(r"""
[marc:]                   # Matches M or underscore
(?P<tag>\d{3,3})        # Matches specific MARC tags
(?P<start>\d{2,2})     # start fixed position
-
(?P<end>\d{2,2})  # End fixed position
""",
                            re.VERBOSE)


class MARCParser(object):

    def __init__(self, **kwargs):
        self.entity_info = {}
        self.record = kwargs.get('record')
        self.redis_datastore = kwargs.get('redis_datastore',
                                          REDIS_DATASTORE)
        self.rules = json.load(
            open(os.path.join(PROJECT_HOME,
                              'bibframe',
                              'ingesters',
                              kwargs.get('rules_filename')),
                 'rb'))

    def add_invalid_value(self,
                          property_name,
                          value):
        """Method adds a value to the redis_datastore invalid
        identifiers set

        Parameters:
        property_name -- property name
        value -- Value to add to set
        """
        

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
                marc_value = []
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
                                marc_value.extend(result)
                                self.test_validity(
                                    marc_pattern,
                                    marc_rule,
                                    property_name,
                                    result)
                if len(marc_value) > 0:
                    self.entity_info[property_name].extend(marc_value)
            if rule.get('post-processing', None):
                self.entity_info[property_name] = [post_processing(
                    self.entity_info[property_name],
                    rule.get('post-processing'))]

    def test_validity(self,
                      current_pattern,
                      marc_rule,
                      property_name,
                      result,
                      key_base='identifiers'):
        """Method takes a marc mapping, tests to see if it invalid, and then
        applies the result to a Redis set for invalid values of property, usually
        an identifier, and saves to a sorted set in the Redis datastore.

        Parameters:
        current_pattern -- Current pattern being evaluated
        property_name -- BIBFRAME entity property
        result -- Result from applying rule to MARC record
        key_base -- Redis key base, defaults to identifiers
        """
        invalid_pattern = marc_rule.get('invalid', [])
        if len(invalid_pattern) > 0 or invalid_pattern.count(marc_rule) < 0:
            return
        redis_key = "{0}:{1}:invalid".format(key_base,
                                             property_name)
        for row in result:
            self.redis_datastore.sadd(redis_key, row)
        

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
                test_result = parse_conditional_field(
                        field,
                        condition_marc_result)
                if condition_result.has_key('method'):

                    for row in test_result:
                        if not hasattr(row,
                                       condition_result.get('method')):
                            return output
                        test_value =  getattr(
                            row,
                            condition_result.get('method'))(
                                condition_result.get('param'))
                        if eval("{0} {1} {2}".format(
                            test_value,
                            operator,
                            condition_result.get('string'))):
                            output.extend(
                                parse_variable_field(
                                    field,
                                    result))
                            
                elif ['is', '='].count(operator) > 0:
                    test_result = parse_variable_field(
                        field,
                        condition_marc_result)
                    test_condition = [condition_result.get('string'),]
                    if test_result == test_condition:
                        output.extend(parse_variable_field(field,
                                                 result))
                
    return output

def parse_conditional_field(field,
                            condition_marc_result):
    """Function takes a field and if the condition_marc_result mapping
    includes X in either indicators, iterators through indicators and
    returns a listing of matches.

    Parameter:
    Field -- MARC field
    condition_marc_result -- Regex results from testing condition
    """
    output = []
    test_indicator1 = condition_marc_result.get('ind1')
    test_indicator2 = condition_marc_result.get('ind2')
    if test_indicator1 != 'X' and test_indicator2 != 'X':
        if field.indicators == [test_indicator1, test_indicator2]:
            output = field.get_subfields(
                condition_marc_result.get('subfield'))
    elif test_indicator1 == 'X' and test_indicator2 != 'X':
        if field.indicators[1] == test_indicator2:
            output = field.get_subfields(
                condition_marc_result.get('subfield'))
    elif test_indicator1 != 'X' and test_indicator2 == 'X':
        if field.indicators[0] == test_indicator1:
            output = field.get_subfields(
                condition_marc_result.get('subfield'))
    return output
        

def parse_fixed_field(field, re_dict):
    """Function takes a MARC21 field and the Regex dictgroup
    for the fixed field and returns a list of values after
    doing a look-up on supporting codes

    Parameters:
    field -- MARC21 field
    re_dict -- Regular Expression dictgroup
    """
    output = []
    if re_dict.has_key('start'):
        # Range operation on fixed field
        tag = re_dict.get('tag')
        if tag != field.tag:
            return output
        start = re_dict.get('start')
        end = re_dict.get('end')
        range_value = field.data[int(start):int(end)+1]
        if range_value is not None:
            output.append(range_value)
    if field.data[0] == re_dict.get('code'):
        tag = re_dict.get('tag')
        code = re_dict.get('code')
        position = re_dict.get('position')
        position_code = field.data[int(re_dict.get('position'))]
        if not MARC_FIXED_CODES.has_key(tag):
            return output
        if not MARC_FIXED_CODES[tag].has_key(code):
            return output

        if MARC_FIXED_CODES[tag][code].has_key(position):
            output.append(
                MARC_FIXED_CODES[tag][code][position].get(position_code))
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
    var_field_search = MARC_FLD_RE.search(mapping)
    fixed_field_search = MARC_FX_FLD_RE.search(mapping)
    if fixed_field_search is None:
        fixed_field_search = MARC_FX_FLD_RANGE_RE.search(mapping)
    if var_field_search is None and fixed_field_search is None:
        return output
    if fixed_field_search:
        regex_result = fixed_field_search.groupdict()
    elif var_field_search:
        regex_result = var_field_search.groupdict()
    else: # May leader, returns output
        return output
    fields = record.get_fields(regex_result.get('tag'))
    for field in fields:
        if hasattr(field, 'indicators'):
            fld_result = parse_variable_field(field,
                                              regex_result)
            
            
        else:
            fld_result = parse_fixed_field(field,
                                           regex_result)
        if len(fld_result) > 0:
            for row in fld_result:                
                output.append(row)
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
        return ' '.join(result)
    elif type(directive) == dict:
        type_of = directive.get('type')
        value = directive.get('value')
        if type_of == 'delimiter':
            return '{0}'.format(value).join(result)
        elif type_of == 'lang-lookup':
            return [MARC_FIXED_CODES['lang'][code] for code in result]
        elif type_of == 'prepend':
            output = '{0} {1}'.format(value,
                                      ', '.join(result))
            return output
        elif type_of == 'second2last':
            # Used for organizational system
            return "{0}{1}{2}".format(" ".join(result[:-1]),
                                      value,
                                      result[-1])
        
    
    
