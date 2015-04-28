__author__ = 'umar.toseef'
import logging
from expedient.clearinghouse.fapi.communication_tools import *


def get_credentials_from_file(user_name):
    """Returns the _user_ credential for the given user_name."""
    return [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': get_file_contents('%s-cred.xml' % (user_name,))}]

def get_certificate_from_file(user_name):
    """Returns the _user_ certificate for the given user_name."""
    return get_file_contents('%s-cert.pem' % (user_name,))

EXPEDIENT_CREDENTIALS = get_credentials_from_file('expedient')
EXPEDIENT_CERTIFICATE = get_certificate_from_file('expedient')
CBAS_DEBUG = True
if CBAS_DEBUG:
    logger = logging.getLogger('CBAS')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('/var/log/apache2/expedient/clearinghouse/cbas.log')
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
        creds = [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}]
    else:
        creds = EXPEDIENT_CREDENTIALS

    print_debug_message(slice_project_urn)

    create_data = {'SLICE_NAME': slice_name, 'SLICE_DESCRIPTION': slice_desc, 'SLICE_PROJECT_URN': slice_project_urn}
    code, value, output = sa_call('create', ['SLICE', creds, {'fields': create_data}])
    if code == 0:
        slice_urn = value['SLICE_URN']
    else:
        print_debug_message('create_slice()\npcode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
        slice_urn = None

    return slice_urn


def create_project(certificate, credentials, project_name, project_desc):

    create_data = {'PROJECT_EXPIRATION': '2020-03-21T11:35:57Z', 'PROJECT_NAME': project_name, 'PROJECT_DESCRIPTION': project_desc}
    code, value, output = sa_call('create', ['PROJECT', [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}], {'fields': create_data}])

    if code == 0:
        project_urn = value['PROJECT_URN']
    else:
        project_urn = None
        print_debug_message('create_project()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))

    return project_urn


def add_member_to_project(project_urn, to_add_user_urn, to_add_user_certificate, authz_user_urn, authz_user_certificate):

    #Try to lookup project credentials for requesting user; otherwise use Expedient creds
    credentials = get_project_credentials(project_urn, authz_user_urn)

    if credentials:
        creds = [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}]
    else:
        creds = EXPEDIENT_CREDENTIALS

    add_data = {'members_to_add': [{'PROJECT_MEMBER': to_add_user_urn, 'PROJECT_ROLE': 'ADMIN',
                                     'MEMBER_CERTIFICATE': to_add_user_certificate}]}
    code, value, output = sa_call('modify_membership', ['PROJECT', project_urn,
                                                        creds, add_data])

    if not code == 0:
        print_debug_message('add_member_to_project()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))


def remove_member_from_project(project_urn, user_urn, authz_user_urn, authz_user_certificate):

    #Try to lookup project credentials for requesting user; otherwise use Expedient creds
    credentials = get_project_credentials(project_urn, authz_user_urn)

    if credentials:
        creds = [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}]
    else:
        creds = EXPEDIENT_CREDENTIALS

    remove_data = {'members_to_remove' : [{'PROJECT_MEMBER': user_urn}]}
    code, value, output = sa_call('modify_membership', ['PROJECT', project_urn,
                                                        creds, remove_data])

    if not code == 0:
        print_debug_message('remove_member_from_project()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))


def add_member_to_slice(project_urn, slice_urn, to_add_user_urn, to_add_user_certificate, authz_user_urn, authz_user_certificate):

    #Try to lookup project credentials for requesting user; otherwise use Expedient creds
    credentials = get_project_credentials(project_urn, authz_user_urn)

    if credentials:
        creds = [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}]
    else:
        creds = EXPEDIENT_CREDENTIALS

    add_data = {'members_to_add': [{'SLICE_MEMBER': to_add_user_urn, 'SLICE_ROLE' : 'ADMIN',
                                     'MEMBER_CERTIFICATE': to_add_user_certificate}]}
    code, value, output = sa_call('modify_membership', ['SLICE', slice_urn,
                                                        creds, add_data])
    if not code == 0:
        print_debug_message('add_member_to_slice()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))


def remove_member_from_slice(slice_urn, user_urn):
    #TODO: user slice credentials should be used to execute this call
    remove_data = {'members_to_remove' : [{'SLICE_MEMBER': user_urn}]}
    code, value, output = sa_call('modify_membership', ['SLICE', slice_urn,
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
        print_debug_message('get_slice_credentials() FAILED!')
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
        print_debug_message('get_project_credentials() Returned no results!')
        credentials = None

    return credentials


def get_member_info(username, user_details=None):

    lookup_results = lookup_members({'MEMBER_USERNAME': username}, 'MEMBER')
    user_info = None
    ssh_key_pair = None

    if lookup_results:
        for key in lookup_results:
            user_info = lookup_results[key]
            user_info['MEMBER_URN'] = key
    else:
        user_info, ssh_key_pair = register_user(username, user_details)

    if user_info:
        return user_info['MEMBER_URN'], user_info['MEMBER_CERTIFICATE'], \
               user_info['MEMBER_CREDENTIALS'], ssh_key_pair
    else:
        print_debug_message('get_member_info() FAILED!')
        return None

def regenerate_member_creds(user_urn):

    update_data = {'MEMBER_CERTIFICATE': ''}
    code, value, output = ma_call('update', ['MEMBER', user_urn, EXPEDIENT_CREDENTIALS,
                                             {'fields': update_data}])
    if not code == 0:
        print_debug_message('1. regenerate_member_creds()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
        return None

    update_data = {'MEMBER_CERTIFICATE': value['MEMBER_CERTIFICATE']}
    code, _, output = sa_call('update_credentials_for_member', [user_urn, EXPEDIENT_CREDENTIALS,
                                             update_data])
    if not code == 0:
        print_debug_message('2. regenerate_member_creds()\ncode:'+str(code)+'\noutput:'+str(output))
    else:
        return value['MEMBER_CERTIFICATE'], value['MEMBER_CERTIFICATE_KEY'], value['MEMBER_CREDENTIALS']

def regenerate_ssh_keys(user_urn, username, certificate=None, credentials=None):

    pub_key, priv_key = generate_ssh_keys(username)
    code = update_ssh_key(user_urn, pub_key, certificate, credentials)
    if not code == 0:
        print_debug_message('regenerate_ssh_keys()\ncode:'+str(code))
        return None, None
    else:
        return pub_key, priv_key

def lookup(match, object_type, _filter=[], certificate=None, credentials=None):
    options = {}
    if match:
        options['match'] = match
    if _filter:
        options['filter'] = _filter

    if credentials:
        creds = [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}]
    else:
        creds = EXPEDIENT_CREDENTIALS

    value = None
    if object_type in ['SLICE', 'PROJECT']:
        code, value, output = sa_call('lookup', [object_type, creds, options])
        if not code == 0:
            print_debug_message('lookup()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
    else:
        print_debug_message('lookup\nUnsupported Object type:'+object_type)

    return value

def update_ssh_key(user_urn, pub_ssh_key, certificate=None, credentials=None):

    fields = {'KEY_PUBLIC': pub_ssh_key}

    if credentials:
        creds = [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}]
    else:
        creds = EXPEDIENT_CREDENTIALS

    code, value, output = ma_call('update', ['KEY', user_urn, creds, {'fields': fields}])
    if not code == 0:
        print_debug_message('update_ssh_key()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
    return code

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

    if credentials:
        creds = [{'geni_type': 'geni_sfa', 'geni_version':'3', 'geni_value': credentials}]
    else:
        creds = EXPEDIENT_CREDENTIALS

    value = None

    if object_type in ['MEMBER', 'KEY']:
        code, value, output = ma_call('lookup', [object_type, creds, options])
        if not code == 0:
            print_debug_message('lookup_members()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
    elif object_type in ['SLICE', 'PROJECT']:
        code, value, output = sa_call('lookup_members', [object_type, object_urn, creds, options])
        if not code == 0:
            print_debug_message('lookup_members()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
    else:
        print_debug_message('lookup_members()\nUnsupported Object type:'+object_type)

    return value


def register_user(username, user_details):

    pub_ssh_key, priv_ssh_key = generate_ssh_keys(username)

    fields = {'MEMBER_FIRSTNAME':username, 'MEMBER_LASTNAME':username, 'MEMBER_USERNAME':username, 'MEMBER_EMAIL':'', 'KEY_PUBLIC': pub_ssh_key}

    if user_details:
        if 'FIRST_NAME' in user_details:
            fields['MEMBER_FIRSTNAME'] = user_details['FIRST_NAME']
        if 'LAST_NAME' in user_details:
            fields['MEMBER_LASTNAME'] = user_details['LAST_NAME']
        if 'EMAIL' in user_details:
            fields['MEMBER_EMAIL'] = user_details['EMAIL']

    options = ['PROJECT_CREATE', 'SLICE_CREATE', 'resolve', 'info', 'refresh']

    code, value, output = ma_call('create', ['MEMBER', EXPEDIENT_CREDENTIALS, {'fields': fields, 'privileges': options}])
    if not code == 0:
        print_debug_message('register_user()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
        return None
    else:
        return value, [pub_ssh_key, priv_ssh_key]


def print_debug_message(msg):
    if CBAS_DEBUG:
        logger.debug(msg+'\n')

def verify_certificate(cert_str):

    code, value, output = ma_call('verify_certificate', [cert_str, EXPEDIENT_CREDENTIALS])
    if not code == 0:
        print_debug_message('verify_certificate()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
        return False
    else:
        return True

def is_cbas_server_active():

    try:
        code, value, output = sa_call('get_version', [])
        if not code == 0:
            print_debug_message('is_cbas_server_active()\ncode:'+str(code)+'\nvalue:'+str(value)+'\noutput:'+str(output))
            return False
        else:
            return True
    except Exception as e:
        print_debug_message('is_cbas_server_active()\n'+str(e.message))
        return False

def generate_ssh_keys(username, password=None):
    """
    Set the C{ssh_public_key} and C{ssh_private_key} attributes to be
        new keys. Note that the keys are stored in base64.

        @parameter password: password to use to encrypt the private key
        @type password: string
    """
    from paramiko import RSAKey
    from StringIO import StringIO

    key = RSAKey.generate(1024)

    output = StringIO()
    key.write_private_key(output, password=password)
    ssh_private_key = output.getvalue()
    output.close()

    ssh_public_key = "ssh-rsa %s %s" % (key.get_base64(), username)

    return ssh_public_key, ssh_private_key

