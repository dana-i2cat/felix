"""
Created on Jun 19, 2010

@author: jnaous
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from expedient.clearinghouse.fapi.cbas import get_member_info
from expedient.clearinghouse.users.models import UserProfile
from expedient.common.messaging.models import DatedMessage
from expedient.common.permissions.shortcuts import has_permission 
from socket import error as socket_error

import errno


def home(request):
    isSuperUser = False
    if(has_permission(request.user, User, "can_manage_users")):
		isSuperUser = True
  
    if request.session.get("visited") == None:
        showFirstTimeTooltips = True 
        request.session["visited"] = True      
    else:
        showFirstTimeTooltips = False

    #<UT>
    if settings.ENABLE_CBAS:
        try:
            user_profile = UserProfile.get_or_create_profile(request.user)
            user_details = {"FIRST_NAME": user_profile.user.first_name, "LAST_NAME": user_profile.user.last_name, "EMAIL": user_profile.user.email}
            # if not (user_profile.urn and user_profile.certificate and
            #         user_profile.certificate_key and user_profile.credentials):
            urn, cert, creds, ssh_key_pair = get_member_info(str(request.user), user_details)
            user_profile.urn = urn
            user_profile.certificate = cert
            user_profile.credentials = creds
            if ssh_key_pair: # Keys are returned only for new registration
                user_profile.public_ssh_key = ssh_key_pair[0]
                user_profile.private_ssh_key = ssh_key_pair[1]
            user_profile.save()
        except socket_error as serr:
            # Error 111: connection refused
            if serr.errno == errno.ECONNREFUSED:
                DatedMessage.objects.post_message_to_user(
                    "Warning: the clearinghouse is enabled, but its server is not running. You or the administrator should start it",
                    request.user, msg_type=DatedMessage.TYPE_WARNING)
    return direct_to_template(
        request,
        template="expedient/clearinghouse/index.html",
        extra_context={
	    "isSuperUser": isSuperUser,
            "showFirstTimeTooltips": showFirstTimeTooltips,
            "breadcrumbs": (
                ("Home", reverse("home")),
            ),
        }
    )
