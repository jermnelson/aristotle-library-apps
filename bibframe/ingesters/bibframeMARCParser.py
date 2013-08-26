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



MARC_FLD_RE = re.compile(r"""
[M|_]                   # Matches M or underscore
(?P<tag>\d{1,3}        # Matches specific MARC tags
  | X{2,2})
(?P<ind1>\w{1,1})       # Matches indicator 1
(?P<ind2>\w{1,1})       # Matches indicator 2
(?P<subfield>\w{1,1})  # Matches subfield
""",
                         re.VERBOSE)

# Using marc21tordf element names following pattern
# M0411_b
test_
    
