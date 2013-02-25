"""
 :mod:`fabfile` Fabric Aristotle Library Apps deployment and continous integration module
"""
__author__ = "Jeremy Nelson"
from fabric.api import local

def test_all():
    local("./manage.py test")

def prepare_deploy():
    test_all()
