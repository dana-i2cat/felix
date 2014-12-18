'''
@author: jnaous
'''
from django.db import models
from expedient.common.permissions.models import Permittee, ObjectPermission
from expedient.common.permissions.utils import permissions_save_override,\
    permissions_delete_override
from expedient.clearinghouse.aggregate.models import Aggregate
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from expedient.clearinghouse.aggregate.utils import get_aggregate_classes
from expedient.common.ldapproxy.models import LdapProxy
from django.conf import settings
from django.db import transaction
import uuid
import string
import re
from expedient.common.utils.validators import asciiValidator, descriptionLightValidator, projectNameValidator

class ProjectManager(models.Manager):
    """Manager for L{Project} instances.
    
    Add methods to retrieve project querysets.
    """
    
    def get_for_user(self, user):
        """Return projects for which C{user} has some permission.
        
        @param user: The user whose projects we are looking for.
        @type user: C{User}.
        """
        if user.is_superuser:
            return self.all()
        
        permittee = Permittee.objects.get_as_permittee(user)
        
        proj_ids = ObjectPermission.objects.filter_for_class(
            klass=Project, permittees=permittee).values_list(
                "object_id", flat=True)
        return self.filter(id__in=list(proj_ids))


import logging
logger = logging.getLogger("Project.models")


class Project(models.Model):
    '''
    A project is a collection of users working on the same set of slices.
    
    @cvar objects: A L{ProjectManager} instance.
    
    @ivar name: The name of the project
    @type name: L{str}
    @ivar description: Short description of the project
    @type description: L{str}
    @ivar aggregates: Read-only property returning all aggregates that can
        be used by the project (i.e. for which the project has the
        "can_use_aggregate" permission).
    @type aggregates: C{QuerySet} of L{Aggregate}s
    @ivar researchers: Read-only property returning all users that have the
        'researcher' role for the project.
    @type researchers: C{QuerySet} of C{User}s.
    @ivar owners: Read-only property returning all users that have the 'owner'
        role for the project.
    @type owners: C{QuerySet} of C{User}s.
    @ivar members: Read-only property returning all users that have some
        permission in the project.
    @type members: C{QuerySet} of C{User}s.
    @ivar members_as_permittees: Read-only property returning all users
        that have some permission in the project as Permittee instances.
    @type members_as_permittees: C{QuerySet} of L{Permittee}s.
    '''

    objects = ProjectManager()
    
    name = models.CharField(max_length=200, unique=True, validators=[projectNameValidator])
    description = models.TextField(validators=[descriptionLightValidator])
    uuid = models.CharField(max_length=200, default = "", unique=True, editable =False)
    #<UT>
    urn = models.CharField(max_length=200, default="")

    '''
    save = permissions_save_override(
        permittee_kw="user",
        model_func=lambda: Project,
        create_perm="can_create_project",
        edit_perm="can_edit_project",
        delete_perm="can_delete_project",
    )
    delete = permissions_delete_override(
        permittee_kw="user",
        model_func=lambda: Project,
        delete_perm="can_delete_project",
    )
    '''
    # originally, code was save = permissions_save_override (...)
    # in which super(model_func(), self).save(*args, **kwargs) is called
    # thus the save function of our parent class.
    #
    # the inner save function that is return by permissions_save_override
    # calls must_have_permission, which raises an PermissionDenied when
    # saving is not allowed. ==> extending the save functionality does not
    # require checking whether action was allowed or not when this 
    # exception is reaised.

    def save(self, *args, **kwargs):
	permissions_save_override(
        	    permittee_kw="user",
	            model_func=lambda: Project,
        	    create_perm="can_create_project",
	            edit_perm="can_edit_project",
        	    delete_perm="can_delete_project",
	)
        super(Project, self).save(*args, **kwargs)
        if settings.LDAP_STORE_PROJECTS and self.uuid:
                self.sync_netgroup_ldap()

    def delete(self, *args, **kwargs):

        from vt_plugin.models.VM import VM
        if VM.objects.filter(projectId = self.uuid):
            raise Exception("Project still have VMs")

        permissions_delete_override(
            permittee_kw="user",
            model_func=lambda: Project,
            delete_perm="can_delete_project",
        )
        if settings.LDAP_STORE_PROJECTS:
            self.delete_netgroup_ldap()

        super(Project, self).delete(*args, **kwargs)

    def _get_aggregates(self):
        """Get all aggregates that can be used by the project
        (i.e. for which the project has the "can_use_aggregate" permission).
        """
        # Permissions are given to the leaf classes
        agg_ids = []
        agg_classes = get_aggregate_classes()
        permittee = Permittee.objects.get_as_permittee(self)
        for agg_class in agg_classes:
            agg_ids.extend(
                ObjectPermission.objects.filter_for_class(
                    agg_class,
                    permission__name="can_use_aggregate",
                    permittees=permittee,
                ).values_list("object_id", flat=True)
            )
        #TODO: marc comented this 
	return Aggregate.objects.filter(pk__in=agg_ids)
        #return Aggregate.objects
    aggregates=property(_get_aggregates)
    
    def _get_researchers(self):
        """Get all users who have the 'researcher' role for the project"""
        from expedient.clearinghouse.roles.models import ProjectRole
        return ProjectRole.objects.get_users_with_role('researcher', self)
    researchers=property(_get_researchers)
    
    def _get_owners(self):
        """Get all users who have the 'owner' role for the project"""
        from expedient.clearinghouse.roles.models import ProjectRole
        return ProjectRole.objects.get_users_with_role('owner', self)
    owners=property(_get_owners)
    
    def _get_members(self):
        """Get all users who have some permission in the project."""
        user_ids = self._get_permittees().values_list("object_id", flat=True)
        return User.objects.filter(pk__in=list(user_ids))
    members=property(_get_members)
    
    def _get_permittees(self):
        """Get all permittees that have some permission in the project."""
        return Permittee.objects.filter_for_class(User).filter(
            objectpermission__object_type=
                ContentType.objects.get_for_model(Project),
            objectpermission__object_id=self.id,
        ).distinct()
    members_as_permittees=property(_get_permittees)

    def _getSlices(self):
	from expedient.clearinghouse.slice.models import Slice
        return Slice.objects.filter(project=self)
    
    def __unicode__(self):
        s = u"Project %s" % self.name
        return s

    @classmethod
    @models.permalink
    def get_create_url(cls):
        "Returns the URL to create projects"
        return ("project_create",)
    
    @models.permalink
    def get_update_url(self):
        "Returns the URL to update project info"
        return ("project_update", (), {"proj_id": self.id})

    @models.permalink
    def get_detail_url(self):
        "Returns the URL for the project detail page"
        return ("project_detail", (), {"proj_id": self.id})
    
    @models.permalink
    def get_delete_url(self):
        "Returns the URL to delete a project"
        return ("project_delete", (), {"proj_id": self.id})
    
    @models.permalink
    def get_agg_add_url(self):
        "Returns the URL to add an aggregate to a project"
        return ("project_add_agg", (), {"proj_id": self.id})

    @models.permalink
    def get_agg_update_url(self, aggregate):
        "Returns URL to update an aggregate's info related to the project"
        return ("project_update_agg", (), {
            "proj_id": self.id,
            "agg_id": aggregate.id})
    
    @models.permalink
    def get_agg_remove_url(self, aggregate):
        "Returns URL to remove aggregate from project"
        return ("project_remove_agg", (), {
            "proj_id": self.id,
            "agg_id": aggregate.id})
    
    @models.permalink
    def get_member_add_url(self):
        return ("project_member_add", (), {
            "proj_id": self.id})
    
    @models.permalink
    def get_member_update_url(self, user):
        return ("project_member_update", (), {
            "proj_id": self.id,
            "user_id": user.id})

    @models.permalink
    def get_member_remove_url(self, user):
        return ("project_member_remove", (), {
            "proj_id": self.id,
            "user_id": user.id})
    
   
    '''
    LDAP synchronization
    '''
 
    def get_netgroup(self):
        str = 'proj_%s_%s' % (self.uuid, self.name)
        str = string.replace(str,' ','_')
        str = string.replace(str,'\t','__')
        return str

    def get_netgroup_dn(self):
        return 'cn=%s,%s' % (self.get_netgroup(), settings.LDAP_MASTER_USERNETGROUPS)

    def sync_netgroup_ldap (self):
        l = LdapProxy()
        dn = self.get_netgroup_dn()
        cn = self.get_netgroup().encode()
        data = {'objectClass': ['nisNetgroup', 'top'], 'cn': [cn], 'nisNetgroupTriple': []}
        for user in self._get_members():
	    if user.password == "!":
            	logger.debug("New member: "+str(user.username))
            	data['nisNetgroupTriple'].append("(,%s,)" % str(user.username))
            	logger.debug("sync_netgroup_ldap: member: %s" % str(user.username))
        l.create_or_replace (dn, data)        

    def delete_netgroup_ldap(self):
        l = LdapProxy()
        dn = self.get_netgroup_dn()
        l.delete (dn)


