"""
 :mod:`backends` Custom III Authentication Backend for Aristotle Library Apps
"""
__author__ = 'Jeremy Nelson'

import logging
import sys
import urllib2
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User 
from aristotle.settings import ILS_PATRON_URL


class IIIUserBackend(ModelBackend):
    """
    This backend is used with III's Patron API to authenticate a user 
    using a last name and an III identification number.
    """

    def authenticate(self,
                     last_name=None,
                     iii_id=None):
        """
        The ``last_name`` and ``iii_id`` are used to authenticate againest
        the III server using the PatronBot Returns None if ``last_name`` and
         ``iii_id`` fail to authenticate.
        """
        raw_html = urllib2.urlopen(ILS_PATRON_URL.format(iii_id)).read()
        if re.search(r'ERRMSG=',raw_html):
            logging.error("INVALID SEARCH {0}".format(raw_html))
            is_valid = False
        else:
            is_valid = True
        user = None
        if is_valid is True:
            try:
                user = User.objects.get(username=iii_id)
            except User.DoesNotExist:
                user = User(username=iii_id,
                            last_name=last_name,
                            is_active=True)
                user.save()
        return user

    def get_user(self,user_id):
        """
        Takes ``user_id`` and tries to retrieve existing User
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
            
        
        
