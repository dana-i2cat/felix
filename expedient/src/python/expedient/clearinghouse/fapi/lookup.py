from expedient.src.python.expedient.clearinghouse.fapi.communication_tools import *


def ma_call(method_name, params=[], user_name='alice'):
    return api_call(method_name, 'ma/2', params=params, user_name=user_name)

def sa_call(method_name, params=[], user_name='alice'):
    return api_call(method_name, 'sa/2', params=params, user_name=user_name, verbose=verbose)


class lookup_example:

    """
    An Example to show how a user lookup would work with Ohouse
    """
    def lookup(self, match, object_type, _filter =[] ):
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
        code, value, output = ma_call('lookup', [object_type, self._credential_list("admin"), options], user_name="admin")

        return value


    def _credential_list(self, user_name):
        """Returns the _user_ credential for the given user_name."""
        return [{"SFA" : get_creds_file_contents('%s-cred.xml' % (user_name,))}]


if __name__ == "__main__":
    #
    lookup_data = {'KEY_MEMBER' : 'urn:publicid:IDN+test:fp7-ofelia:eu+user+alice'}
    lookup_instance = lookup_example()
    print lookup_instance.lookup(lookup_data,'KEY')
