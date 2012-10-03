'''
Created on Jul 17, 2010

@author: jnaous
'''
import re
from django.core.validators import RegexValidator
from django.forms import ValidationError

mac_re = re.compile(r'^([\dA-Fa-f]{2}:){5}[\dA-Fa-f]{2}$')
validate_mac_address = RegexValidator(mac_re, u'Enter a valid MAC address (in "xx:xx:xx:xx:xx:xx" format).', 'invalid')

ip_re = ipv4_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}(/\d?\d)?$')
validate_ip_prefix = RegexValidator(ip_re, u'Enter a valid MAC address (in "xx:xx:xx:xx:xx:xx" format).', 'invalid')

def resourceNameValidator(s):
    pattern = re.compile("^([0-9a-zA-Z\-\_])+$")
    if (pattern.match(s) == None):
        raise ValidationError("Please do not use accented characters, symbols or whitespaces.")

def numberValidator(s):
    pattern = re.compile("^([0-9])+$")
    if (pattern.match(s) == None):
        raise ValidationError("Please use numbers only.")

def asciiValidator(s):
    pattern = re.compile("^([0-9a-zA-Z\-\_\ ])+$")
    if (pattern.match(s) == None):
        raise ValidationError("Please do not use accented characters and avoid using \'@\'.")

#def asciiValidator(s):
#    for c in s:
#        if ord(c)>127 or c == '@':
#            raise ValidationError("Please use only non accented characters and avoid using \'@\'.")
