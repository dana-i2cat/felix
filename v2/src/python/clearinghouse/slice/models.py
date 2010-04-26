from django.db import models
from clearinghouse.project.models import Project
from clearinghouse.extendable.models import Extendable

class Slice(models.Model):
    '''
    Holds information about reservations across aggregates
    @param name: The name of the Slice
    @type name: L{str}
    @param description: Short description of the slice
    @type description: L{str}
    @param project: Project in which this slice belongs
    @type project: L{models.ForeignKey} to L{Project}
    '''

    name = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project)
    
class GenericAggregateSliceInfo(Extendable):
    '''
    Holds additional aggregate-specific information about the slice
    
    @param slice: the slice to which the info is related
    @type slice: L{models.ForeignKey} to L{Slice}
    '''
    slice = models.ForeignKey(Slice)
    
    class Meta:
        abstract = True

