'''
Created on Jun 19, 2010

@author: jnaous
'''
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from expedient.common.permissions.shortcuts import has_permission 
from django.contrib.auth.models import User
from expedient.clearinghouse.users.models import UserProfile
from expedient.clearinghouse.fapi.cbas import *
from expedient.clearinghouse.defaultsettings.cbas import *

def home(request):

    isSuperUser = False
    if(has_permission(request.user, User, "can_manage_users")):
		isSuperUser = True
  
    if request.session.get('visited') == None:
        showFirstTimeTooltips = True 
        request.session['visited'] = True      
    else:
        showFirstTimeTooltips = False

    #<UT>
    if ENABLE_CBAS:
        user_profile = UserProfile.get_or_create_profile(request.user)

        # if not (user_profile.urn and user_profile.certificate and
        #         user_profile.certificate_key and user_profile.credentials):
        urn, cert, cert_key, creds = get_member_info(str(request.user))
        user_profile.urn = urn
        user_profile.certificate = cert
        user_profile.certificate_key = cert_key
        user_profile.credentials = creds
        user_profile.save()


    return direct_to_template(
        request,
        template='expedient/clearinghouse/index.html',
        extra_context={
	    "isSuperUser": isSuperUser,
            "showFirstTimeTooltips" :  showFirstTimeTooltips,
            "breadcrumbs": (
                ("Home", reverse("home")),
            ),
        }
    )
