"""
 :mod:`commands` Order Redis Commands
"""
__author__ = 'Jeremy Nelson'
import re,redis,pymarc
import datetime,sys
from app_settings import REDIS_HOST,REDIS_PORT
from invoice.redis_helpers import ingest_invoice

redis_server = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
PCARD_RE = re.compile(r"^Inv#\sPCARD\s(?P<number>\d+\w+)\sDated:(?P<date>\d+-\d+-\d+)\sAmt:\$(?P<amount>\d+[,|.]*\d*)\sOn:(?P<paid>\d+-\d+-\d+)\sVoucher#(?P<voucher>\d+)")
INVOICE_RE = re.compile(r"^Inv#\s(?P<number>\d+\w+)\sDated:(?P<date>\d+-\d+-\d+)\sAmt:\$(?P<amount>\d+[,|.]*\d*)\sOn:(?P<paid>\d+-\d+-\d+)\sVoucher#(?P<voucher>\d+)$")

def get_or_add_voucher(voucher_name):
    voucher_key = redis_server.hget('invoice:vouchers',
                                    voucher_name)
    if voucher_key is None:
        voucher_key = 'voucher:%s' % redis_server.incr('global:voucher')
        redis_server.hset('invoice:vouchers',
                          voucher_id,
                          voucher_key)
        redis_server.hset(voucher_key,
                          'name',
                          voucher_name)
    return voucher_key

def add_transaction(regex_result,bib_number,parent_key):
    """
    Function adds a transaction to the datastore

    :param regex_result: Results from the either Invoice or pcard regular
                         expression on the 994 field
    :param bib_number: Bibliographic ID Number
    :param parent_key: Parent Redis key
    :rtype string: New redis key for the transaction
    """ 
    # Creates a transaction to associate with invoice
    transaction_key = 'transaction:%s' % redis_server.incr('global:transaction')
    # Converts dates to python datetimes and set in redis
    transaction_date = datetime.datetime.strptime(regex_result.get('date'),
                                                  '%m-%d-%y')
    redis_server.hset(transaction_key,'date',transaction_date)
    if not redis_server.hexists(parent_key,'transaction-date'):
        redis_server.hset(parent_key,'transaction-date')
    # Sets date whent the transaction was paid on
    paid_on_date = datetime.datetime.strptime(regex_result.get('paid'),
                                              '%m-%d-%y')
    redis_server.hset(transaction_key,'paid-on',paid_on_date)
    # Set invoice key and amount to transaction hash
    redis_server.hset(transaction_key,'bib-number',bib_number)
    redis_server.hset(transaction_key,'invoice',invoice_key)
    redis_server.hset(transaction_key,'amount',invoice_result.get('amount'))
    # Add to invoice:transactions sorted set by date
    redis_server.zadd('%s:transactions' % invoice_key,
                      transaction_date.toordinal(),
                      transaction_key)

def ingest_pcard(marc_record):
    """
    Function ingests a III Order MARC Record Invoice into Redis datastore.

    :param marc_record: MARC record
    :rtype: dictionary
    """
    if marc_record['035']:
        raw_bib = marc_record['035']['a']
        bib_number = raw_bib[1:-1]
    pcard_regex = PCARD.search(marc_record['995']['a'])
    if pcard_regex is not None:
        pcard_result = pcard_regex.groupdict()
        pcard_number = pcard_result.pop('number')
        pcard_key = redis_server.hget('pcard:numbers',
                                      pcard_result['number'])
        if pcard_key is None:
           pcard_key = 'pcard:%s' % redis_server.incr("global:pcard")
           redis_server.hset('pcard:numbers',
                             pcard_number,
                             pcard_key)
    
           
            
                                 
           
           
        


def load_order_records(pathname):
    """
    Function takes a path to a MARC file location, creates an iterator,
    and attempts to ingest invoice or pcard from each record

    :param pathname: Path to MARC file
    """
    marc_reader = pymarc.MARCReader(open(pathname),
                                    utf8_handling='ignore')
    for counter,record in enumerate(marc_reader):
        if counter%1000:
            sys.stderr.write(".")
        else:
            sys.stderr.write("%s" % counter)
        if record['995']:
            field995a = record['995']['a']
            if PCARD_RE.search(field995a):
                ingest_pcard(record)
            elif INVOICE_RE.search(field995a):
                ingest_invoice(record)
        
                          
            
            
        
        

    
                             
    
    
