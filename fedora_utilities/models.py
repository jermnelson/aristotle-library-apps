"""
  :mod:`fedora_batch.models` Module contains models using Django and Fedora
  Commons for basic batch operatiosn for repository management.
"""

from django.db import models
from django.contrib.auth.models import User

class BatchIngestLog(models.Model):
    """
    :class:`BatchIngestLog` logs batch ingest of objects into
    Fedora Commons repository.
    """
    created_on = models.DateTimeField(auto_now_add=True)
    fedora_url = models.URLField()
    pids = models.ManyToManyField('PersisentIdentifer')

class BatchModifyMetadataLog(models.Model):
    """
    :class:`BatchModifyMetadataLog` logs all batch metadata modifications
    to one or more objects in the Fedora Commons repository.
    """
    created_on = models.DateTimeField(auto_now_add=True)
    fedora_url = models.URLField()
    metadata = models.TextField()
    pids = models.ManyToManyField('PersisentIdentifer')

class ObjectMovementLog(models.Model):
    """
    :class:`ObjectMovementLog` logs `PersisentIdentifer` movement within the Fedora 
    Commons Digital Repository
    """
    collection_pid = models.ForeignKey('PersisentIdentifer',
                                       related_name="new_collection")
    created_on = models.DateTimeField(auto_now_add=True)
    source_pid = models.ForeignKey('PersisentIdentifer')


class PersisentIdentifer(models.Model):
    """
    :class:`PersisentIdentifer` or PID, is used to track app activity with
    the Fedora Commons server.
    """
    created_on = models.DateTimeField(auto_now_add=True)
    fedora_url = models.URLField()
    identifier = models.CharField(max_length=50)
    



