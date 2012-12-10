"""
 :mod:`redis_helpers` module provides generic Redis helper functionality for
 all apps.
"""
__author__ = 'Jeremy Nelson'


def generate_redis_protocal(*args):
    """
    Helper function generates Redis Protocal
    """
    proto = ''
    proto += '*{0}\r\n'.format(str(len(args)))
    for arg in args:
        arg = str(arg)
        proto += '${0}\r\t'.format(str(len(arg)))
        proto += '{0}\r\n'.format(str(arg))
    return proto
