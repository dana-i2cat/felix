'''
@author: bpuype

copyright 2014-2015 FP7 FELIX, iMinds

'''

from urlparse import urlparse


def add_basic_auth(uri, username=None, password=None):
    parsed = urlparse(uri.lower())
    if username:
        if password:
            new_url = "%s://%s:%s@%s%s" % (parsed.scheme,
                                           username,
                                           password,
                                           parsed.netloc,
                                           parsed.path)
        else:
            new_url = "%s://%s@%s%s" % (parsed.scheme,
                                        username,
                                        parsed.netloc,
                                        parsed.path)
    else:
        new_url = uri
    return new_url

