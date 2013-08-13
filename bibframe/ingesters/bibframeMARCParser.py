__author__ = "Jeremy Nelson"

from pyparsing import alphas, nums, dblQuotedString, Combine, Word, Group, delimitedList, Suppress, removeQuotes


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

