from django.contrib.auth.views import login
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.models import User
import OpenSSL.crypto
from Crypto.Util import asn1
from django.conf import settings
from expedient.clearinghouse.fapi.cbas import verify_certificate
import binascii

class ScriptsRemoteUserMiddleware(object):

        def process_request(self, request):
            if not request.POST.has_key('cert') or not request.POST.has_key('key') or not request.POST.has_key('csrfmiddlewaretoken'):
                return None

            cert_str = request.POST.get('cert')
            sign_str = request.POST.get('key')
            token = request.POST.get('csrfmiddlewaretoken')

            if not cert_str or not sign_str or not token:
                return None

            myBackend = ScriptsRemoteUserBackend()
            user = myBackend.authenticate(cert_str, sign_str, token)

            if not user:
                return None

            auth.login(request, user)

            if request.user.is_authenticated():
                # They're already authenticated --- go ahead and redirect
                redirect_field_name = REDIRECT_FIELD_NAME
                redirect_to = request.REQUEST.get(redirect_field_name, '')
                if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
                    redirect_to = settings.LOGIN_REDIRECT_URL
                return HttpResponseRedirect(redirect_to)


class ScriptsRemoteUserBackend(object):

    def authenticate(self, cert_str, sign_str, token):
        #if not settings.ENABLE_CBAS:
        #    return None
        user_urn = self.verify_signature(cert_str, sign_str, token)
        if not user_urn:
            return None
        username = self.clean_username(user_urn)

        if username:
            valid = verify_certificate(cert_str)
            if not valid:
                return None
        else:
            return None

        user, created = User.objects.get_or_create(username=username,)
        if created:
            user.save()
        user.backend = 'mit.ScriptsRemoteUserBackend'
        return user

    def verify_signature(self, cert_str, sig_str, token):

        user_urn = None

        try:
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_str)
            sign = binascii.unhexlify(sig_str)
            OpenSSL.crypto.verify(cert, sign, str(token), 'sha512')
            sub = cert.get_subject()
            user_urn = str(sub.commonName)
        except Exception as e:
            pass

        return user_urn

    def verify_key_cert_pair(self, cert_str, key_str):

        c=OpenSSL.crypto
        cert = None
        key = None
        try:
            cert = c.load_certificate(c.FILETYPE_PEM, cert_str)
            key = c.load_privatekey(c.FILETYPE_PEM, key_str)
        except:
            pass

        if not cert or not key:
            return None

        pub=cert.get_pubkey()

        # Only works for RSA (I think)
        if pub.type()!=c.TYPE_RSA or key.type()!=c.TYPE_RSA:
            raise Exception('Can only handle RSA keys')

        # This seems to work with public as well
        pub_asn1=c.dump_privatekey(c.FILETYPE_ASN1, pub)
        priv_asn1=c.dump_privatekey(c.FILETYPE_ASN1, key)

        # Decode DER
        pub_der=asn1.DerSequence()
        pub_der.decode(pub_asn1)
        priv_der=asn1.DerSequence()
        priv_der.decode(priv_asn1)

        # Get the modulus
        pub_modulus=pub_der[1]
        priv_modulus=priv_der[1]

        if pub_modulus==priv_modulus:
            sub = cert.get_subject()
            return str(sub.commonName)
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def clean_username(self, username, ):
        if username and username.startswith(settings.CBAS_HOST_NAME+'.user'):
            i = username.rfind("user.")
            if i > 0:
                return username[i+5:]
        return username


# def scripts_login(request, **kwargs):
#     host = request.META['HTTP_HOST'].split(':')[0]
#
#     if host in ('localhost', '127.0.0.1'):
#         #return login(request, **kwargs)
#         return None
#     elif request.META['SERVER_PORT'] == '443':
#         if request.user.is_authenticated():
#             # They're already authenticated --- go ahead and redirect
#             if 'redirect_field_name' in kwargs:
#                 redirect_field_name = kwargs['redirect_field_names']
#             else:
#                 from django.contrib.auth import REDIRECT_FIELD_NAME
#                 redirect_field_name = REDIRECT_FIELD_NAME
#             redirect_to = request.REQUEST.get(redirect_field_name, '')
#             if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
#                 redirect_to = settings.LOGIN_REDIRECT_URL
#             return HttpResponseRedirect(redirect_to)
#         else:
#             return login(request, **kwargs)
#     else:
#         # Move to port 444
#         redirect_to = "https://%s:443%s" % (host, request.META['REQUEST_URI'], )
#         return HttpResponseRedirect(redirect_to)

