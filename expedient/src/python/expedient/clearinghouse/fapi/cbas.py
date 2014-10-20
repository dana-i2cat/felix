__author__ = 'umar.toseef'
import logging
from expedient.clearinghouse.fapi.communication_tools import *


def get_credentials_from_file(user_name):
    """Returns the _user_ credential for the given user_name."""
    return [{"SFA" : get_file_contents('%s-cred.xml' % (user_name,))}]

def get_certificate_from_file(user_name):
    """Returns the _user_ certificate for the given user_name."""
    return get_file_contents('%s-cert.pem' % (user_name,))

EXPEDIENT_CREDENTIALS = get_credentials_from_file('expedient')
EXPEDIENT_CERTIFICATE = get_certificate_from_file('expedient')
logger = logging.getLogger('CBAS')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/var/log/apache2/cbas.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

def ma_call(method_name, params=[]):

    return api_call(method_name, 'ma/2', params=params)


def sa_call(method_name, params=[]):
    return api_call(method_name, 'sa/2', params=params)


def create_slice(owner_urn, owner_certificate, slice_name, slice_desc, slice_project_urn):

    #Try to lookup project credentials for requesting user; otherwise use Expedient creds
    credentials = get_project_credentials(slice_project_urn, owner_urn)

    if credentials:
        cert = owner_certificate
        creds = [{"SFA": credentials}]
    else:
        cert = EXPEDIENT_CERTIFICATE
        creds = EXPEDIENT_CREDENTIALS

    logger.info(slice_project_urn)

    create_data = {'SLICE_NAME': slice_name, 'SLICE_DESCRIPTION': slice_desc, 'SLICE_PROJECT_URN': slice_project_urn}
    code, value, output = sa_call('create', ['SLICE', cert, creds, {'fields': create_data}])
    if code == 0:
        slice_urn = value['SLICE_URN']
    else:
        logger.debug('create_slice()\npcode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
        slice_urn = None

    return slice_urn


def create_project(certificate, credentials, project_name, project_desc):

    create_data = {'PROJECT_EXPIRATION': '2020-03-21T11:35:57Z', 'PROJECT_NAME': project_name, 'PROJECT_DESCRIPTION': project_desc}
    code, value, output = sa_call('create', ['PROJECT', certificate, [{"SFA": credentials}], {'fields': create_data}])

    if code == 0:
        project_urn = value['PROJECT_URN']
    else:
        project_urn = None
        logger.debug('create_project()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))

    return project_urn


def add_member_to_project(project_urn, to_add_user_urn, to_add_user_certificate, authz_user_urn, authz_user_certificate):

    #Try to lookup project credentials for requesting user; otherwise use Expedient creds
    credentials = get_project_credentials(project_urn, authz_user_urn)

    if credentials:
        cert = authz_user_certificate
        creds = [{"SFA": credentials}]
    else:
        cert = EXPEDIENT_CERTIFICATE
        creds = EXPEDIENT_CREDENTIALS

    add_data = {'members_to_add': [{'PROJECT_MEMBER': to_add_user_urn, 'PROJECT_ROLE': 'ADMIN',
                                     'MEMBER_CERTIFICATE': to_add_user_certificate}]}
    code, value, output = sa_call('modify_membership', ['PROJECT', project_urn, cert,
                                                        creds, add_data])

    if not code == 0:
        logger.debug('add_member_to_project()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))


def remove_member_from_project(project_urn, user_urn, authz_user_urn, authz_user_certificate):

    #Try to lookup project credentials for requesting user; otherwise use Expedient creds
    credentials = get_project_credentials(project_urn, authz_user_urn)

    if credentials:
        cert = authz_user_certificate
        creds = [{"SFA": credentials}]
    else:
        cert = EXPEDIENT_CERTIFICATE
        creds = EXPEDIENT_CREDENTIALS

    remove_data = {'members_to_remove' : [{'PROJECT_MEMBER': user_urn}]}
    code, value, output = sa_call('modify_membership', ['PROJECT', project_urn, cert,
                                                        creds, remove_data])

    if not code == 0:
        logger.debug('remove_member_from_project()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))


def add_member_to_slice(project_urn, slice_urn, to_add_user_urn, to_add_user_certificate, authz_user_urn, authz_user_certificate):

    #Try to lookup project credentials for requesting user; otherwise use Expedient creds
    credentials = get_project_credentials(project_urn, authz_user_urn)

    if credentials:
        cert = authz_user_certificate
        creds = [{"SFA": credentials}]
    else:
        cert = EXPEDIENT_CERTIFICATE
        creds = EXPEDIENT_CREDENTIALS

    add_data = {'members_to_add': [{'SLICE_MEMBER': to_add_user_urn, 'SLICE_ROLE' : 'ADMIN',
                                     'MEMBER_CERTIFICATE': to_add_user_certificate}]}
    code, value, output = sa_call('modify_membership', ['SLICE', slice_urn, cert,
                                                        creds, add_data])
    if not code == 0:
        logger.debug('add_member_to_slice()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))


def remove_member_from_slice(slice_urn, user_urn):
    #TODO: user slice credentials should be used to execute this call
    remove_data = {'members_to_remove' : [{'SLICE_MEMBER': user_urn}]}
    code, value, output = sa_call('modify_membership', ['SLICE', slice_urn, EXPEDIENT_CERTIFICATE,
                                                        EXPEDIENT_CREDENTIALS, remove_data])
    return code, value, output


def get_slice_credentials(project_urn, slice_urn, user_urn, user_certificate):

    lookup_results = lookup_members(match={'SLICE_MEMBER': user_urn}, object_type='SLICE', object_urn=slice_urn)

    if not lookup_results:
        add_member_to_slice(project_urn, slice_urn, user_urn, user_certificate, user_urn, user_certificate)
        lookup_results = lookup_members(match={'SLICE_MEMBER': user_urn}, object_type='SLICE', object_urn=slice_urn)

    if lookup_results:
        membership_info = lookup_results[0]
        return membership_info['SLICE_CREDENTIALS']
    else:
        logger.debug('get_slice_credentials() FAILED!')
        return None


def get_project_credentials(project_urn, user_urn):

    """

    :rtype : object
    """
    lookup_results = lookup_members(match={'PROJECT_MEMBER': user_urn}, object_type='PROJECT', object_urn=project_urn)

    if lookup_results:
        membership_info = lookup_results[0]
        credentials = membership_info['PROJECT_CREDENTIALS']
    else:
        logger.debug('get_project_credentials() Returned no results!')
        credentials = None

    return credentials


def get_member_info(username):

    lookup_results = lookup_members({'MEMBER_USERNAME': username}, 'MEMBER')
    user_info = None

    if lookup_results:
        for key in lookup_results:
            user_info = lookup_results[key]
            user_info['MEMBER_URN'] = key
    else:
        user_info = register_user(username)

    if user_info:
        return user_info['MEMBER_URN'], user_info['MEMBER_CERTIFICATE'], \
               user_info['MEMBER_CERTIFICATE_KEY'], user_info['MEMBER_CREDENTIALS']
    else:
        logger.debug('get_member_info() FAILED!')
        return None


def lookup(match, object_type, _filter=[], certificate=None, credentials=None):
    options = {}
    if match:
        options['match'] = match
    if _filter:
        options['filter'] = _filter

    if not (certificate and credentials):
        certificate = EXPEDIENT_CERTIFICATE
        credentials = EXPEDIENT_CREDENTIALS

    value = None
    if object_type in ['SLICE', 'PROJECT']:
        code, value, output = sa_call('lookup', [object_type, certificate, credentials, options])
        if not code == 0:
            logger.debug('lookup()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
    else:
        logger.debug('lookup\nUnsupported Object type:'+object_type)

    return value

def lookup_members(match, object_type, _filter=[], object_urn=None, certificate=None, credentials=None):
    """
    A sample lookup function which uses dumb ssl certificates and credentials
    Args:
        match: objects to match on e.g., member / user urn
    Return:
        return the result of the event generated
    """
    options = {}
    if match:
        options['match'] = match
    if _filter:
        options['filter'] = _filter

    if not (certificate and credentials):
        certificate = EXPEDIENT_CERTIFICATE
        credentials = EXPEDIENT_CREDENTIALS

    value = None

    if object_type in ['MEMBER', 'KEY']:
        code, value, output = ma_call('lookup', [object_type, certificate, credentials, options])
        if not code == 0:
            logger.debug('lookup_members()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
    elif object_type in ['SLICE', 'PROJECT']:
        code, value, output = sa_call('lookup_members', [object_type, object_urn, certificate, credentials, options])
        if not code == 0:
            logger.debug('lookup_members()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
    else:
        logger.debug('lookup_members()\nUnsupported Object type:'+object_type)

    return value


def register_user(username):

    fields = {'MEMBER_FIRSTNAME':username, 'MEMBER_LASTNAME':username, 'MEMBER_USERNAME':username, 'MEMBER_EMAIL':''}
    options = ['CAN_CREATE_PROJECT']

    code, value, output = ma_call('create', ['MEMBER', EXPEDIENT_CERTIFICATE, EXPEDIENT_CREDENTIALS, {'fields': fields, 'privileges': options}])
    if not code == 0:
        logger.debug('code:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
        return None
    else:
        return value


def print_debug_message(msg):
    logger.debug(msg)
    pass
