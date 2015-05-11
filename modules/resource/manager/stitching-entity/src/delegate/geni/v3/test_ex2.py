from delegate_v3 import GENIv3Delegate
from delegate.geni.v3.se_scheduler import SESchedulerService
import se_configurator as SEConfigurator
from nose import with_setup
from datetime import datetime, timedelta

  

def allocate_setup_function():

    
    global slice_urn 
    global client_cert 
    global credentials 
    global rspec
    global se_manifest
    global se_slivers
    global se_scheduler 
    global rspec
    global end_time 
    
    se_scheduler = SESchedulerService()
    
    slice_urn ='urn:publicid:IDN+geni:gpo:gcf+slice+myslice3'
    client_cert ='None'
    end_time ='2015-05-27 11:31:00.520000'
    credentials ="""[{'geni_value': '<?xml version="1.0" encoding="utf-8"?>\n<signed-credential xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.planet-lab.org/resources/sfa/credential.xsd" xsi:schemaLocation="http://www.planet-lab.org/resources/sfa/ext/policy/1 http://www.planet-lab.org/resources/sfa/ext/policy/1/policy.xsd"><credential xml:id="ref0"><type>privilege</type><serial>8</serial><owner_gid>-----BEGIN CERTIFICATE-----\nMIICNDCCAZ2gAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTQxMTIwMTQzODEzWhcNMTkxMTE5\nMTQzODEzWjAkMSIwIAYDVQQDExlnZW5pLy9ncG8vL2djZi51c2VyLmFsaWNlMIGf\nMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/NsR8UXXh4BYIywsSl7F9LtbPszAP\n2MZxmlkLAJiFCgDYHIzTAk/wgrrYE++ozxNNRxes153z9nv4i3tj0DEsWZ4OULz+\n8dy0ELn4L5GSfoQVSkQ7iOl63RJUTNePHy6vjGsynWPN5KlMpbwjQxeasZ7r9mAT\nSua7VisKV8ZCdQIDAQABo3QwcjAMBgNVHRMBAf8EAjAAMGIGA1UdEQRbMFmGKHVy\nbjpwdWJsaWNpZDpJRE4rZ2VuaTpncG86Z2NmK3VzZXIrYWxpY2WGLXVybjp1dWlk\nOjg4NzJkZTM4LTQ3NDEtNGE2OC05OTliLWMyOGE2NTUyNTIwNjANBgkqhkiG9w0B\nAQQFAAOBgQB1xp/MSU6fgMFh+fRtLL5ZiOt13NTVH/fOG/cmJEmrtV9npqq4MgsY\nGTQP+y1dOXcIq+6Cjoxutx7o8zWWnpB+WDSXHev0V2YgtZRH54lmIvAflOwfgblV\n+XKVYVVFyTpLclEJosA5KXSJBeWo7C6GlMazFDJzcRqxioh8MT3Bzw==\n-----END CERTIFICATE-----\n</owner_gid><owner_urn>urn:publicid:IDN+geni:gpo:gcf+user+alice</owner_urn><target_gid>-----BEGIN CERTIFICATE-----\nMIICPDCCAaWgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTUwMzIwMTQyNzAyWhcNMjAwMzE4\nMTQyNzAyWjAoMSYwJAYDVQQDEx1nZW5pLy9ncG8vL2djZi5zbGljZS5teXNsaWNl\nMzCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAt5mH/GzUtzA2QhVu7+6HDSrn\nv1k8PIKOKiUzTxI0oEKJAxlJKAex1y5HNAMpW0suwPds35sAIzzyTqKXRgJOnc7k\noRNBIDTpZJvfrd8LZcaOaD6OWgGfWKQV5dbH+55oUJokHAjYQIWaOTwsNZNHPpDj\nPGWy4954NnpjQnkEgqsCAwEAAaN4MHYwDAYDVR0TAQH/BAIwADBmBgNVHREEXzBd\nhix1cm46cHVibGljaWQ6SUROK2dlbmk6Z3BvOmdjZitzbGljZStteXNsaWNlM4Yt\ndXJuOnV1aWQ6NDUyMTNjMmYtNzQ2Mi00ODQzLTgwMjYtYmFiNjJhYjI1MzBiMA0G\nCSqGSIb3DQEBBAUAA4GBAJPJELU/A4wORZliFeZU8USJo7s/6iy5sciyHhJyJg3/\nlYnv6mBaePEiDo/PSTQkUQ8GQYPM/U/SQd/o0Bxm2hOLmnuuz2DWjvydBD8x4lNX\nin8WC6aqOMj0VChDzSH01sFAfLL64BKyTFuPqgez6IbyI6ujMFcEjyapDiMAWUU7\n-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----\nMIICOzCCAaSgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTQxMTIwMTQzODEzWhcNMTkxMTE5\nMTQzODEzWjAmMSQwIgYDVQQDExtnZW5pLy9ncG8vL2djZi5hdXRob3JpdHkuc2Ew\ngZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKDR6ValqucemYx5LK/ZbxiePVQM\n0NNY0GbKELFeGuiUow9CMYlh73i0pd9aDY16e/44SWPDgY+0GQNGfUdcV/lYhljR\nXThvk5f/XLQEBDEz2iQDIFGstQ5bDiBFO1hmZ0Xzgf+JVgl4QA8BhtT8RDU7vr7V\nb1SYDubW8ou7wb4VAgMBAAGjeTB3MA8GA1UdEwEB/wQFMAMBAf8wZAYDVR0RBF0w\nW4YqdXJuOnB1YmxpY2lkOklETitnZW5pOmdwbzpnY2YrYXV0aG9yaXR5K3Nhhi11\ncm46dXVpZDplZTljYzUyYS1iNGY2LTRhZDItOGJjNS1iODkyNWZlZTJkYWYwDQYJ\nKoZIhvcNAQEEBQADgYEAX2i0t5/s1ZIMDi+mAwUiayUQdVp3EPmToIvH/NN07snP\nbHZZiyvEqaGYgXbX9DUFKCwBvVGwelTSvVucqmo28vBeoLpGKcb/4xJhllfPKRHb\nrCzC3htVn9HfuRfQIT8rP7wBjc0eNl1ImjogpVm8gOXK4lw62nguQsq+vfb3ejQ=\n-----END CERTIFICATE-----\n</target_gid><target_urn>urn:publicid:IDN+geni:gpo:gcf+slice+myslice3</target_urn><uuid/><expires>2015-05-06T14:33:28Z</expires><privileges><privilege><name>refresh</name><can_delegate>true</can_delegate></privilege><privilege><name>embed</name><can_delegate>true</can_delegate></privilege><privilege><name>bind</name><can_delegate>true</can_delegate></privilege><privilege><name>control</name><can_delegate>true</can_delegate></privilege><privilege><name>info</name><can_delegate>true</can_delegate></privilege></privileges></credential><signatures><Signature xmlns="http://www.w3.org/2000/09/xmldsig#" xml:id="Sig_ref0">\n  <SignedInfo>\n    <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>\n    <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>\n    <Reference URI="#ref0">\n      <Transforms>\n        <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>\n      </Transforms>\n      <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>\n      <DigestValue>ZLvP+b8grJYGkbEoNBur0NqL8Ts=</DigestValue>\n    </Reference>\n  </SignedInfo>\n  <SignatureValue>V0txZxUSlzfrJ3oFzYBvoUcVQNA4XltKf0X4NfS9+PiLsRuRYOTMbJq5RbUXRGei\nCWMAItvxD6R0lKDEOEaIPkqtsmHzWYFGd8Z+X1jz0iVsS3DZPyMbWMClPOmNV0gj\nYE2TtXYt6lMBvHshKutGA57u+5gqGegZu1q1Ocz+UEk=</SignatureValue>\n  <KeyInfo>\n    <X509Data>\n      \n      \n      \n    <X509Certificate>MIICOzCCAaSgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTQxMTIwMTQzODEzWhcNMTkxMTE5\nMTQzODEzWjAmMSQwIgYDVQQDExtnZW5pLy9ncG8vL2djZi5hdXRob3JpdHkuc2Ew\ngZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKDR6ValqucemYx5LK/ZbxiePVQM\n0NNY0GbKELFeGuiUow9CMYlh73i0pd9aDY16e/44SWPDgY+0GQNGfUdcV/lYhljR\nXThvk5f/XLQEBDEz2iQDIFGstQ5bDiBFO1hmZ0Xzgf+JVgl4QA8BhtT8RDU7vr7V\nb1SYDubW8ou7wb4VAgMBAAGjeTB3MA8GA1UdEwEB/wQFMAMBAf8wZAYDVR0RBF0w\nW4YqdXJuOnB1YmxpY2lkOklETitnZW5pOmdwbzpnY2YrYXV0aG9yaXR5K3Nhhi11\ncm46dXVpZDplZTljYzUyYS1iNGY2LTRhZDItOGJjNS1iODkyNWZlZTJkYWYwDQYJ\nKoZIhvcNAQEEBQADgYEAX2i0t5/s1ZIMDi+mAwUiayUQdVp3EPmToIvH/NN07snP\nbHZZiyvEqaGYgXbX9DUFKCwBvVGwelTSvVucqmo28vBeoLpGKcb/4xJhllfPKRHb\nrCzC3htVn9HfuRfQIT8rP7wBjc0eNl1ImjogpVm8gOXK4lw62nguQsq+vfb3ejQ=</X509Certificate>\n<X509SubjectName>CN=geni//gpo//gcf.authority.sa</X509SubjectName>\n<X509IssuerSerial>\n<X509IssuerName>CN=geni//gpo//gcf.authority.sa</X509IssuerName>\n<X509SerialNumber>3</X509SerialNumber>\n</X509IssuerSerial>\n</X509Data>\n    <KeyValue>\n<RSAKeyValue>\n<Modulus>\noNHpVqWq5x6ZjHksr9lvGJ49VAzQ01jQZsoQsV4a6JSjD0IxiWHveLSl31oNjXp7\n/jhJY8OBj7QZA0Z9R1xX+ViGWNFdOG+Tl/9ctAQEMTPaJAMgUay1DlsOIEU7WGZn\nRfOB/4lWCXhADwGG1PxENTu+vtVvVJgO5tbyi7vBvhU=\n</Modulus>\n<Exponent>\nAQAB\n</Exponent>\n</RSAKeyValue>\n</KeyValue>\n  </KeyInfo>\n</Signature></signatures></signed-credential>\n', 'geni_version': '3', 'geni_type': 'geni_sfa'}] <?xml version="1.1" encoding="UTF-8"?>"""

    rspec ="""<?xml version="1.1" encoding="UTF-8"?>
<rspec type="request"
       xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1"
       xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
       xs:schemaLocation="http://www.geni.net/resources/rspec/3/request.xsd
            http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd">

    <node client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01"
          component_manager_id="urn:publicid:IDN+fms:psnc:serm+authority+cm">
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1+vlan"
                                         vlantag="1000"/>
        </interface>
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2+vlan"
                                         vlantag="2000"/>
         </interface>
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3+vlan"
                                         vlantag="3000"/>
        </interface>
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4+vlan"
                                         vlantag="4000"/>
        </interface>
    </node>

    <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2">
        <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
        <link_type name="urn:felix+vlan_trans"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2"/>
     </link>
        <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3_00:00:00:00:00:00:00:01_4">
        <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
        <link_type name="urn:felix+vlan_trans"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4"/>
    </link>
</rspec>
"""

    se_manifest = """<rspec xmlns:xs="http://www.w3.org/2001/XMLSchema-instance" xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1" xmlns="http://www.geni.net/resources/rspec/3" xs:schemaLocation="http://www.geni.net/resources/rspec/3/manifest.xsd http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd" type="manifest">
  <node client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01" component_manager_id="urn:publicid:IDN+fms:psnc:serm+authority+cm">
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1">
      <sharedvlan:link_shared_vlan vlantag="1000" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1+vlan"/>
    </interface>
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2">
      <sharedvlan:link_shared_vlan vlantag="2000" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2+vlan"/>
    </interface>
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3">
      <sharedvlan:link_shared_vlan vlantag="3000" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3+vlan"/>
    </interface>
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4">
      <sharedvlan:link_shared_vlan vlantag="4000" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4+vlan"/>
    </interface>
  </node>
  <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2" sliver_id="urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2_1000_2000" vlantag="1000-2000">
    <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
    <link_type name="urn:felix+vlan_trans"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2"/>
  </link>
  <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3_00:00:00:00:00:00:00:01_4" sliver_id="urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_3_00:00:00:00:00:00:00:01_4_3000_4000" vlantag="3000-4000">
    <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
    <link_type name="urn:felix+vlan_trans"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_3"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4"/>
  </link>
</rspec>
"""

    se_slivers=[{'geni_operational_status': 'geni_notready', 'geni_expires': u'2015-05-27 11:31:00.520000', 'geni_allocation_status': u'geni_allocated', 'geni_sliver_urn': u'urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2_1000_2000'}, {'geni_operational_status': 'geni_notready', 'geni_expires': u'2015-05-27 11:31:00.520000', 'geni_allocation_status': u'geni_allocated', 'geni_sliver_urn': u'urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_3_00:00:00:00:00:00:00:01_4_3000_4000'}]

    return se_manifest, slice_urn, client_cert, credentials, rspec
    

def allocate_vlan_case_setup_function():

    
    global slice_urn 
    global client_cert 
    global credentials 
    global rspec
    global se_manifest
    global se_slivers
    global se_scheduler 
    global rspec
    global end_time 
    
    se_scheduler = SESchedulerService()
    
    slice_urn ='urn:publicid:IDN+geni:gpo:gcf+slice+myslice3'
    client_cert ='None'
    end_time ='2015-05-27 11:31:00.520000'
    credentials ="""[{'geni_value': '<?xml version="1.0" encoding="utf-8"?>\n<signed-credential xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.planet-lab.org/resources/sfa/credential.xsd" xsi:schemaLocation="http://www.planet-lab.org/resources/sfa/ext/policy/1 http://www.planet-lab.org/resources/sfa/ext/policy/1/policy.xsd"><credential xml:id="ref0"><type>privilege</type><serial>8</serial><owner_gid>-----BEGIN CERTIFICATE-----\nMIICNDCCAZ2gAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTQxMTIwMTQzODEzWhcNMTkxMTE5\nMTQzODEzWjAkMSIwIAYDVQQDExlnZW5pLy9ncG8vL2djZi51c2VyLmFsaWNlMIGf\nMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/NsR8UXXh4BYIywsSl7F9LtbPszAP\n2MZxmlkLAJiFCgDYHIzTAk/wgrrYE++ozxNNRxes153z9nv4i3tj0DEsWZ4OULz+\n8dy0ELn4L5GSfoQVSkQ7iOl63RJUTNePHy6vjGsynWPN5KlMpbwjQxeasZ7r9mAT\nSua7VisKV8ZCdQIDAQABo3QwcjAMBgNVHRMBAf8EAjAAMGIGA1UdEQRbMFmGKHVy\nbjpwdWJsaWNpZDpJRE4rZ2VuaTpncG86Z2NmK3VzZXIrYWxpY2WGLXVybjp1dWlk\nOjg4NzJkZTM4LTQ3NDEtNGE2OC05OTliLWMyOGE2NTUyNTIwNjANBgkqhkiG9w0B\nAQQFAAOBgQB1xp/MSU6fgMFh+fRtLL5ZiOt13NTVH/fOG/cmJEmrtV9npqq4MgsY\nGTQP+y1dOXcIq+6Cjoxutx7o8zWWnpB+WDSXHev0V2YgtZRH54lmIvAflOwfgblV\n+XKVYVVFyTpLclEJosA5KXSJBeWo7C6GlMazFDJzcRqxioh8MT3Bzw==\n-----END CERTIFICATE-----\n</owner_gid><owner_urn>urn:publicid:IDN+geni:gpo:gcf+user+alice</owner_urn><target_gid>-----BEGIN CERTIFICATE-----\nMIICPDCCAaWgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTUwMzIwMTQyNzAyWhcNMjAwMzE4\nMTQyNzAyWjAoMSYwJAYDVQQDEx1nZW5pLy9ncG8vL2djZi5zbGljZS5teXNsaWNl\nMzCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAt5mH/GzUtzA2QhVu7+6HDSrn\nv1k8PIKOKiUzTxI0oEKJAxlJKAex1y5HNAMpW0suwPds35sAIzzyTqKXRgJOnc7k\noRNBIDTpZJvfrd8LZcaOaD6OWgGfWKQV5dbH+55oUJokHAjYQIWaOTwsNZNHPpDj\nPGWy4954NnpjQnkEgqsCAwEAAaN4MHYwDAYDVR0TAQH/BAIwADBmBgNVHREEXzBd\nhix1cm46cHVibGljaWQ6SUROK2dlbmk6Z3BvOmdjZitzbGljZStteXNsaWNlM4Yt\ndXJuOnV1aWQ6NDUyMTNjMmYtNzQ2Mi00ODQzLTgwMjYtYmFiNjJhYjI1MzBiMA0G\nCSqGSIb3DQEBBAUAA4GBAJPJELU/A4wORZliFeZU8USJo7s/6iy5sciyHhJyJg3/\nlYnv6mBaePEiDo/PSTQkUQ8GQYPM/U/SQd/o0Bxm2hOLmnuuz2DWjvydBD8x4lNX\nin8WC6aqOMj0VChDzSH01sFAfLL64BKyTFuPqgez6IbyI6ujMFcEjyapDiMAWUU7\n-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----\nMIICOzCCAaSgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTQxMTIwMTQzODEzWhcNMTkxMTE5\nMTQzODEzWjAmMSQwIgYDVQQDExtnZW5pLy9ncG8vL2djZi5hdXRob3JpdHkuc2Ew\ngZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKDR6ValqucemYx5LK/ZbxiePVQM\n0NNY0GbKELFeGuiUow9CMYlh73i0pd9aDY16e/44SWPDgY+0GQNGfUdcV/lYhljR\nXThvk5f/XLQEBDEz2iQDIFGstQ5bDiBFO1hmZ0Xzgf+JVgl4QA8BhtT8RDU7vr7V\nb1SYDubW8ou7wb4VAgMBAAGjeTB3MA8GA1UdEwEB/wQFMAMBAf8wZAYDVR0RBF0w\nW4YqdXJuOnB1YmxpY2lkOklETitnZW5pOmdwbzpnY2YrYXV0aG9yaXR5K3Nhhi11\ncm46dXVpZDplZTljYzUyYS1iNGY2LTRhZDItOGJjNS1iODkyNWZlZTJkYWYwDQYJ\nKoZIhvcNAQEEBQADgYEAX2i0t5/s1ZIMDi+mAwUiayUQdVp3EPmToIvH/NN07snP\nbHZZiyvEqaGYgXbX9DUFKCwBvVGwelTSvVucqmo28vBeoLpGKcb/4xJhllfPKRHb\nrCzC3htVn9HfuRfQIT8rP7wBjc0eNl1ImjogpVm8gOXK4lw62nguQsq+vfb3ejQ=\n-----END CERTIFICATE-----\n</target_gid><target_urn>urn:publicid:IDN+geni:gpo:gcf+slice+myslice3</target_urn><uuid/><expires>2015-05-06T14:33:28Z</expires><privileges><privilege><name>refresh</name><can_delegate>true</can_delegate></privilege><privilege><name>embed</name><can_delegate>true</can_delegate></privilege><privilege><name>bind</name><can_delegate>true</can_delegate></privilege><privilege><name>control</name><can_delegate>true</can_delegate></privilege><privilege><name>info</name><can_delegate>true</can_delegate></privilege></privileges></credential><signatures><Signature xmlns="http://www.w3.org/2000/09/xmldsig#" xml:id="Sig_ref0">\n  <SignedInfo>\n    <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>\n    <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>\n    <Reference URI="#ref0">\n      <Transforms>\n        <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>\n      </Transforms>\n      <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>\n      <DigestValue>ZLvP+b8grJYGkbEoNBur0NqL8Ts=</DigestValue>\n    </Reference>\n  </SignedInfo>\n  <SignatureValue>V0txZxUSlzfrJ3oFzYBvoUcVQNA4XltKf0X4NfS9+PiLsRuRYOTMbJq5RbUXRGei\nCWMAItvxD6R0lKDEOEaIPkqtsmHzWYFGd8Z+X1jz0iVsS3DZPyMbWMClPOmNV0gj\nYE2TtXYt6lMBvHshKutGA57u+5gqGegZu1q1Ocz+UEk=</SignatureValue>\n  <KeyInfo>\n    <X509Data>\n      \n      \n      \n    <X509Certificate>MIICOzCCAaSgAwIBAgIBAzANBgkqhkiG9w0BAQQFADAmMSQwIgYDVQQDExtnZW5p\nLy9ncG8vL2djZi5hdXRob3JpdHkuc2EwHhcNMTQxMTIwMTQzODEzWhcNMTkxMTE5\nMTQzODEzWjAmMSQwIgYDVQQDExtnZW5pLy9ncG8vL2djZi5hdXRob3JpdHkuc2Ew\ngZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAKDR6ValqucemYx5LK/ZbxiePVQM\n0NNY0GbKELFeGuiUow9CMYlh73i0pd9aDY16e/44SWPDgY+0GQNGfUdcV/lYhljR\nXThvk5f/XLQEBDEz2iQDIFGstQ5bDiBFO1hmZ0Xzgf+JVgl4QA8BhtT8RDU7vr7V\nb1SYDubW8ou7wb4VAgMBAAGjeTB3MA8GA1UdEwEB/wQFMAMBAf8wZAYDVR0RBF0w\nW4YqdXJuOnB1YmxpY2lkOklETitnZW5pOmdwbzpnY2YrYXV0aG9yaXR5K3Nhhi11\ncm46dXVpZDplZTljYzUyYS1iNGY2LTRhZDItOGJjNS1iODkyNWZlZTJkYWYwDQYJ\nKoZIhvcNAQEEBQADgYEAX2i0t5/s1ZIMDi+mAwUiayUQdVp3EPmToIvH/NN07snP\nbHZZiyvEqaGYgXbX9DUFKCwBvVGwelTSvVucqmo28vBeoLpGKcb/4xJhllfPKRHb\nrCzC3htVn9HfuRfQIT8rP7wBjc0eNl1ImjogpVm8gOXK4lw62nguQsq+vfb3ejQ=</X509Certificate>\n<X509SubjectName>CN=geni//gpo//gcf.authority.sa</X509SubjectName>\n<X509IssuerSerial>\n<X509IssuerName>CN=geni//gpo//gcf.authority.sa</X509IssuerName>\n<X509SerialNumber>3</X509SerialNumber>\n</X509IssuerSerial>\n</X509Data>\n    <KeyValue>\n<RSAKeyValue>\n<Modulus>\noNHpVqWq5x6ZjHksr9lvGJ49VAzQ01jQZsoQsV4a6JSjD0IxiWHveLSl31oNjXp7\n/jhJY8OBj7QZA0Z9R1xX+ViGWNFdOG+Tl/9ctAQEMTPaJAMgUay1DlsOIEU7WGZn\nRfOB/4lWCXhADwGG1PxENTu+vtVvVJgO5tbyi7vBvhU=\n</Modulus>\n<Exponent>\nAQAB\n</Exponent>\n</RSAKeyValue>\n</KeyValue>\n  </KeyInfo>\n</Signature></signatures></signed-credential>\n', 'geni_version': '3', 'geni_type': 'geni_sfa'}] <?xml version="1.1" encoding="UTF-8"?>"""

    rspec ="""<?xml version="1.1" encoding="UTF-8"?>
<rspec type="request"
       xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1"
       xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"
       xs:schemaLocation="http://www.geni.net/resources/rspec/3/request.xsd
            http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd">

    <node client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01"
          component_manager_id="urn:publicid:IDN+fms:psnc:serm+authority+cm">
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1+vlan"
                                         vlantag="1100"/>
        </interface>
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2+vlan"
                                         vlantag="2100"/>
         </interface>
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1+vlan"
                                         vlantag="3100"/>
        </interface>
        <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4">
            <sharedvlan:link_shared_vlan name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4+vlan"
                                         vlantag="4100"/>
        </interface>
    </node>

    <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2">
        <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
        <link_type name="urn:felix+vlan_trans"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2"/>
     </link>
        <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_4">
        <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
        <link_type name="urn:felix+vlan_trans"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1"/>
        <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4"/>
    </link>
</rspec>
"""

    se_manifest = """<rspec xmlns:xs="http://www.w3.org/2001/XMLSchema-instance" xmlns:sharedvlan="http://www.geni.net/resources/rspec/ext/shared-vlan/1" xmlns="http://www.geni.net/resources/rspec/3" xs:schemaLocation="http://www.geni.net/resources/rspec/3/manifest.xsd http://www.geni.net/resources/rspec/ext/shared-vlan/1/request.xsd" type="manifest">
  <node client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01" component_manager_id="urn:publicid:IDN+fms:psnc:serm+authority+cm">
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1">
      <sharedvlan:link_shared_vlan vlantag="1100" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1+vlan"/>
    </interface>
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2">
      <sharedvlan:link_shared_vlan vlantag="2100" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2+vlan"/>
    </interface>
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1">
      <sharedvlan:link_shared_vlan vlantag="3100" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1+vlan"/>
    </interface>
    <interface client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4">
      <sharedvlan:link_shared_vlan vlantag="4100" name="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4+vlan"/>
    </interface>
  </node>
  <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2" sliver_id="urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2_1100_2100" vlantag="1100-2100">
    <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
    <link_type name="urn:felix+vlan_trans"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_2"/>
  </link>
  <link client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_4" sliver_id="urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_4_3100_4100" vlantag="3100-4100">
    <component_manager name="urn:publicid:IDN+AIST+authority+serm"/>
    <link_type name="urn:felix+vlan_trans"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_1"/>
    <interface_ref client_id="urn:publicid:IDN+fms:psnc:serm+datapath+00:00:00:00:00:00:00:01_4"/>
  </link>
</rspec>
"""

    se_slivers=[{'geni_operational_status': 'geni_notready', 'geni_expires': u'2015-05-27 11:31:00.520000', 'geni_allocation_status': u'geni_allocated', 'geni_sliver_urn': u'urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_2_1100_2100'}, {'geni_operational_status': 'geni_notready', 'geni_expires': u'2015-05-27 11:31:00.520000', 'geni_allocation_status': u'geni_allocated', 'geni_sliver_urn': u'urn:publicid:IDN+fms:psnc:serm+sliver+00:00:00:00:00:00:00:01_1_00:00:00:00:00:00:00:01_4_3100_4100'}]

    return se_manifest, slice_urn, client_cert, credentials, rspec


def allocate_teardown_function1():
    se_scheduler.stop()
    slice_urn = ""
    client_cert = ""
    credentials = ""
    rspec = ""
    se_manifest =""
    se_slivers = ""
    #se_scheduler 
    rspec = ""
    end_time = ""
    
       
 
def allocate_teardown_function2():
    se_scheduler.stop()
    slice_urn = ""
    client_cert = ""
    credentials = ""
    rspec = ""
    se_manifest =""
    se_slivers = ""
    #se_scheduler 
    rspec = ""
    end_time = ""

def allocate_teardown_function3():
    se_scheduler.stop()
    slice_urn = ""
    client_cert = ""
    credentials = ""
    rspec = ""
    se_manifest =""
    se_slivers = ""
    #se_scheduler 
    rspec = ""
    end_time = ""

def allocate_teardown_function4():
    se_scheduler.stop()
    slice_urn = ""
    client_cert = ""
    credentials = ""
    rspec = ""
    se_manifest =""
    se_slivers = ""
    #se_scheduler 
    rspec = ""
    end_time = ""
      
@with_setup(allocate_setup_function, allocate_teardown_function1)   
def test_manifest_after_allocate_with_two_link():
    #se_manifest, slice_urn, client_cert, credentials = allocate_setup_function()
    #se_conf = SEConfigurator.seConfigurator("../../../../conf/se-config_test.yaml")
    geni= GENIv3Delegate()
    #geni.SEResources = se_conf
    man,sliv = geni.allocate(slice_urn, client_cert, credentials,
                 rspec, end_time)
    
    assert  man == se_manifest
    
@with_setup(allocate_setup_function, allocate_teardown_function2)   
def test_sliver_after_allocate_with_two_link():
    geni= GENIv3Delegate()
    man,sliv = geni.allocate(slice_urn, client_cert, credentials,
                 rspec, end_time) 
    assert  sliv == se_slivers
    
@with_setup(allocate_vlan_case_setup_function, allocate_teardown_function3)   
def test_sliver_after_allocate_with_two_vlan_on_same_interface():
    geni= GENIv3Delegate()
    man,sliv = geni.allocate(slice_urn, client_cert, credentials,
                 rspec, end_time) 
    assert  sliv == se_slivers
                 
@with_setup(allocate_vlan_case_setup_function, allocate_teardown_function4)   
def test_manifest_after_allocate_with_two_vlan_on_same_interface():
    geni= GENIv3Delegate()
    man,sliv = geni.allocate(slice_urn, client_cert, credentials,
                 rspec, end_time) 
    assert  man == se_manifest
    
                 
                 
