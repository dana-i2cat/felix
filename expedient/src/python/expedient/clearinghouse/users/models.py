'''
Created on Dec 3, 2009

@author: jnaous
'''

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    '''
    Additional information about a user.
    
    @ivar user: the user to whom this UserProfile belongs
    @type user: L{auth.models.User}
    @ivar affiliation: The organization to which the user is affiliated
    @type affiliation: L{str}
    '''

    user                   = models.ForeignKey(User, unique=True)
    affiliation            = models.CharField(max_length=100, default="")
    #<UT>
    credentials            = models.TextField(max_length=10000, default="")
    certificate = models.TextField(max_length=10000, default="")
    certificate_key = models.TextField(max_length=1000, default="")
    urn = models.CharField(max_length=200, default="")

    def __unicode__(self):
        try:
            return "Profile for %s" % self.user
        except:
            return "No user"
    
    @classmethod
    def get_or_create_profile(cls, user):
        '''
        Gets the user's profile if available or creates one if one doesn't exist
        
        @param user: the User whose UserProfile to get or create
        @type user: L{auth.models.User}
        
        @return: user's profile
        @rtype: L{UserProfile} 
        '''
        
        try:
            profile = user.get_profile()
        except UserProfile.DoesNotExist:
            profile = cls.objects.create(
                            user=user,
                            )
        return profile
