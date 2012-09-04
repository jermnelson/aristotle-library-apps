"""
 :mod:`commands` Order Redis Commands
"""
__author__ = 'Jeremy Nelson'
import re,redis,pymarc
import datetime,sys
from app_settings import REDIS_HOST,REDIS_PORT,REDIS_PASSWORD

redis_server = redis.StrictRedis(host=REDIS_HOST,
                                 port=REDIS_PORT,
                                 password=REDIS_PASSWORD)
PCARD_RE = re.compile(r"^Inv#\sPCARD\s(?P<number>\d+\w+)\sDated:(?P<date>\d+-\d+-\d+)\sAmt:\$(?P<amount>\d+[,|.]*\d*)\sOn:(?P<paid>\d+-\d+-\d+)\sVoucher#(?P<voucher>\d+)")
INVOICE_RE = re.compile(r"^Inv#\s(?P<number>\d+\w+)\sDated:(?P<date>\d+-\d+-\d+)\sAmt:\$(?P<amount>\d+[,|.]*\d*)\sOn:(?P<paid>\d+-\d+-\d+)\sVoucher#(?P<voucher>\d+)$")

def get_or_add_voucher(voucher_name):
    voucher_key = redis_server.hget('invoice:vouchers',
                                    voucher_name)
    if voucher_key is None:
        voucher_key = 'voucher:%s' % redis_server.incr('global:voucher')
        redis_server.hset('invoice:vouchers',
                          voucher_name,
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
    transaction_pipeline = redis_server.pipeline()
    # Converts dates to python datetimes and set in redis
    transaction_date = datetime.datetime.strptime(regex_result.get('date'),
                                                  '%m-%d-%y')
    transaction_pipeline.hset(transaction_key,'date',transaction_date)
    if not redis_server.hexists(parent_key,'transaction-date'):
        transaction_pipeline.hset(parent_key,
                                  'transaction-date',
                                  transaction_date)
    # Sets date whent the transaction was paid on
    paid_on_date = datetime.datetime.strptime(regex_result.get('paid'),
                                              '%m-%d-%y')
    transaction_pipeline.hset(transaction_key,'paid_on',paid_on_date)
    # Sets bib number and amount to transaction hash
    transaction_pipeline.hset(transaction_key,'bib_number',bib_number)
    transaction_pipeline.hset(transaction_key,'amount',regex_result.get('amount'))
    # Add to entity:transactions sorted set by date
    transaction_pipeline.zadd('%s:transactions' % parent_key,
                              transaction_date.toordinal(),
                              transaction_key)
    # Add to orders sorted set
    transaction_pipeline.zadd('orders',
                              transaction_date.toordinal(),
                              parent_key)
    transaction_pipeline.execute()
    return transaction_key

def get_entity(**kwargs):
    """
    Function takes either an entity number or the redis key for the
    entity and returns a dictionary with the entity information and
    all associated transactions.

    :param number: entity number, optional
    :param redis_key: entity redis_key, optional
    :rtype: dictionary
    """
    # redis_key variable scoped to function, starts with None
    redis_key = None
    # If an invoice number parameter, try to retrieve redis_key
    # from the invoice:numbers Redis hash
    if kwargs.has_key('number'):
        number = kwargs.get('number')
        #! This may run into some collusion if the same number exists
        #! for both invoice and pcard number hashes
        if redis_server.hexists('pcard:numbers',number):
            redis_key = redis_server.hget('pcard:numbers',
                                          number)
        elif redis_server.hexists('invoice:numbers',
                                  number):
            redis_key = redis_server.hget('invoice:numbers',
                                          kwargs.get('number'))
    # If an invoice redis_key paramter, first checks consistency
    # and then set func redis_key variable to passed
    if kwargs.has_key('redis_key'):
        direct_redis_key = kwargs.get('redis_key')
        # Checks to see if redis_key param exists in current datastore,
        # raises error if it doesn't
        if not redis_server.exists(direct_redis_key):
            raise ValueError('%s redis key does not exist in datastore' %\
                             direct_redis_key)
        # Should only be set if the code calling this func passes in both
        # an invoice number and a redis_key
        if redis_key is not None:
            # Raise error if the entity number redis_key differs from
            # passed in redis_key
            if redis_key != direct_redis_key:
                error_msg = 'redis_key of %s not equal to passed in redis_key of %s' %\
                            (redis_key,
                             direct_redis_key)
                raise ValueError(error_msg)
        else:
            # Finally, sets the func redis_key variable to passed in redis_key
            redis_key = direct_redis_key
    redis_info = redis_server.hgetall(redis_key)
    redis_info['redis_key'] = redis_key
    # Extracts all transactions associated with this invoice
    redis_transactions = redis_server.zrange('%s:transactions' % redis_key,
                                             0,
                                             -1)
    # Add a list of transaction dicts to redis_info dict
    # also computes and returns total amount for the invoice
    redis_info['transactions'] = []
    total_amt = 0
    for transaction_key in redis_transactions:
        transaction = redis_server.hgetall(transaction_key)
        clean_transaction = dict()
        # Add transaction amount to invoice total
        total_amt += float(transaction.get('amount'))
        # Remove invoice or pcard from transaction and check to confirm that
        # transaction is for the correct invoice
        if transaction.has_key('pcard'):
            transaction_entity_key = transaction.pop('pcard')
        elif transaction.has_key('invoice'):
            transaction_entity_key = transaction.pop('invoice')
        if  transaction_entity_key != redis_key:
            raise ValueError("Wrong invoice for %s" % transaction_key)
        clean_transaction['redis_key'] = transaction_key
        for k,v in transaction.iteritems():
           template_key = k.replace(" ","_")
           if template_key in ["date","paid_on"]:
               clean_transaction[template_key] = datetime.datetime.strptime(v,
                                                                            '%Y-%m-%d 00:00:00')
           else:
               clean_transaction[template_key] = v
        redis_info['transactions'].append(clean_transaction)
    redis_info['total_amount'] = total_amt
    # Return redis_info to calling code
    return redis_info

def get_order_slice(entity_key,slice_size=5):
    """
    Helper function retrieves a number of past orders based on either a
    invoice key or pcard key.

    :param entity_key: Redis key of either the invoice or pcard
    :param slice_size: Number of orders, default is 5
    """
    entity_slice = []
    entity_list = entity_key.split(":")
    entity_root = entity_list[0]
    incr_num = int(entity_list[1])
    for i in range(incr_num,incr_num-5,-1):
        redis_key = '%s:%s' % (entity_root,i)
        if redis_server.exists(redis_key) is True:
            entity = {'%s_key' % entity_root:redis_key}
            entity['number'] = redis_server.hget(redis_key,'number')
            last_transaction = redis_server.zrange('%s:transactions' % redis_key,
                                                   -1,
                                                   -1)
            if len(last_transaction) > 0:
                last_transaction = last_transaction[0]
                raw_date = redis_server.hget(last_transaction,
                                             'date')
                entity['date'] = datetime.datetime.strptime(raw_date,
                                                            '%Y-%m-%d 00:00:00')
            entity_slice.append(entity)
    return entity_slice

def get_voucher(voucher_key):
    output = {'voucher':redis_server.hgetall(voucher_key)}
    transaction_keys = redis_server.zrange("%s:transactions" % voucher_key,0,-1)
    transactions = []
    for row in transaction_keys:
        transactions.append(redis_server.hgetall(row))
    output['transactions'] = transactions
    return output

def ingest_invoice(marc_record):
    """
    Function ingests a III Order MARC Record Invoice into Redis datastore.

    :param marc_record: MARC record
    :rtype: dictionary
    """
    if marc_record['035']:
        raw_bib = marc_record['035']['a']
        bib_number = raw_bib[1:-1]
    if marc_record['995']:
        invoice_regex = INVOICE_RE.search(marc_record['995']['a'])
    else:
        print("ERROR cannot extract invoice number from %s" % marc_record.leader)
        invoice_regex = None
    if invoice_regex is not None:
        invoice_result = invoice_regex.groupdict()
        
        # Checks to see if invoice exists, add otherwise
        invoice_key = redis_server.hget('invoice:numbers',
                                        invoice_result['number'])
        if invoice_key is None:
            invoice_key = 'invoice:%s' % redis_server.incr('global:invoice')
            redis_server.hset('invoice:numbers',
                              invoice_result.get('number'),
                              invoice_key)
        # Checks if invoice number is present, add otherwise to invoice
        if not redis_server.exists(invoice_key):
            redis_server.hset(invoice_key,
                              'number',
                              invoice_result.get('number'))
            redis_server.hset(invoice_key,
                              'created',
                              datetime.datetime.today())

        # Adds transaction and adds to invoice
        transaction_key = add_transaction(invoice_result,
                                          bib_number,
                                          invoice_key)
        redis_server.hset(transaction_key,'invoice',invoice_key)
        # Checks exists or adds voucher
        voucher_key = get_or_add_voucher(invoice_result.get('voucher'))
        redis_server.hset(transaction_key,'voucher',voucher_key)

def ingest_pcard(marc_record):
    """
    Function ingests a III Order MARC Record Invoice into Redis datastore.

    :param marc_record: MARC record
    :rtype: dictionary
    """
    if marc_record['035']:
        raw_bib = marc_record['035']['a']
        bib_number = raw_bib[1:-1]
    pcard_regex = PCARD_RE.search(marc_record['995']['a'])
    if pcard_regex is not None:
        pcard_result = pcard_regex.groupdict()
        pcard_number = pcard_result.pop('number')
        pcard_key = redis_server.hget('pcard:numbers',
                                      pcard_number)
        if pcard_key is None:
           pcard_key = 'pcard:%s' % redis_server.incr("global:pcard")
           redis_server.hset('pcard:numbers',
                             pcard_number,
                             pcard_key)
        # Adds transaction and adds to invoice
        transaction_key = add_transaction(pcard_result,
                                          bib_number,
                                          pcard_key)
        redis_server.hset(transaction_key,'pcard',pcard_key)
        # Checks exists or adds voucher
        voucher_key = get_or_add_voucher(pcard_result.get('voucher'))
        redis_server.hset(transaction_key,'voucher',voucher_key)

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
        
                          
            
            
        
        

    
                             
    
    
