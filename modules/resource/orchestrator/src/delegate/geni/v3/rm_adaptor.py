"""
Includes dummy methods that will disappear as delegates are properly filled.
TODO: Replace with necessary adaptor against C RM GENI API.
"""

def get_all_leases():
    return []

def extend_lease(lease, expiration_time):
    pass

def leases_in_slice(urn):
    return []

def reserve_lease(rip, slice_urn, client_uuid, client_email, end_time):
    pass
