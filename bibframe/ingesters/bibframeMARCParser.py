__author__ = "Jeremy Nelson"

from pyparsing import alphas, nums, dblQuotedString, Combine, Word, Group, delimitedList, Suppress, removeQuotes
import re

bibframeMARCMap = None
def getbibframeMARCMap():
    global bibframeMARCMap

    if bibframeMARCMap is None:        
        tag = Word( nums, min=3, max=3 )
        subfields = delimitedList(Word("$", alphas), "+")
        subfield_conditional = Word( "/", alphas ) | Word(",", alphas)
        field_range = nums + "XX"


test_maps = {'manufacture': '260 $e+$f+$g',
             'subject': '6XX, 043',
             'title': '245 $a',
             'upi': '0247-+2"uri"/a,z'}



    
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


def conditional_MARC21(record, rule):
    """Function takes a conditional and a mapping dict (called a rule)
    and returns the result if the test condition matches the antecedient
    
    Parameters:
    record -- MARC21 record
    rule -- Rule to match MARC field on
    """
    if rule.has_key('conditional'):
        conditional = BASIC_CONDITIONAL_RE.search(
            rule.get('conditional'))
        if conditional is None:
            conditional = METHOD_CONDITIONAL_RE.search(
                rule.get('conditional'))
        condition_result = conditional.groupdict()
        marc_values = parse_MARC21(record,
                                   condition_result.get('marc'))
        if condition_result.has_key('method'):
            for value in marc_values:
                method_value = getattr(value,
                                       condition_result.get('method'))(
                                           condition_result.get('param'))
                value = method_value
        operator = condition_result.get('operator')
        if len(marc_values) > 0:
            for row in marc_values:
                if ['is', '='].count(operator) > 0:
                    if row == condition_result.get('string'):
                        return parse_MARC21(
                            record,
                            rule.get('map'))
                elif operator == '>':
                    if row > condition_result.get('string'):
                        return parse_MARC21(
                            record,
                            rule.get('map'))
                elif operator == '<':
                    if row < condition_result.get('string'):
                        return parse_MARC21(
                            record,
                            rule.get('map'))
                
                    
                    
            
            


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
    result = search.groupdict()
    fields = record.get_fields(result.get('tag'))
    for field in fields:
        test_ind1 = result.get('ind1').replace("_", " ")
        test_ind2 = result.get('ind2').replace("_", " ")
        if field.indicators == [test_ind1,
                                test_ind2]:
            subfields = field.get_subfields(result.get('subfield'))
            output.extend(subfields)
    return output
    
    
