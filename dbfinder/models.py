__author__ = "Diane Westerfield"
__author__ = "Jeremy Nelson"

from django.db import models

class AlternativeTitle(models.Model):
    database = models.ForeignKey('Database')
    title = models.CharField(max_length=255)
    

class Database(models.Model):
    description = models.TextField()
    subjects = models.ManyToManyField('Subject')
    title = models.CharField(max_length=255)
    url = models.URLField()
    

class Subject(models.Model):
    name = models.CharField(max_length=150)
    
    
    
    
