import logging
'''
	@author: msune

	Ofelia XEN Agent settings file (Static settings) 
'''
##General Parameters

'''Base folder where vms and logs will be store.
All the rest of folder must be inside this folder'''
OXA_PATH="/mnt/l1vm/image/dc1-1/"

'''Log folder. Must exist!'''
OXA_LOG="/var/log/"

#Log level. Should be: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
#Default warning
LOG_LEVEL="DEBUG"

'''XMLRPC over HTTPS server parameters'''
#XMLRPC_SERVER_LISTEN_HOST='127.0.0.1' # You should not use '' here, unless you have a real FQDN.
XMLRPC_SERVER_LISTEN_HOST='0.0.0.0' # You should not use '' here, unless you have a real FQDN.
XMLRPC_SERVER_LISTEN_PORT=9229

XMLRPC_SERVER_KEYFILE='security/certs/agent.key'    # Replace with your PEM formatted key file
XMLRPC_SERVER_CERTFILE='security/certs/agent.crt'  # Replace with your PEM formatted certificate file

#HDs
OXA_DEFAULT_SWAP_SIZE_MB=512


##Ofelia Debian VM configurator parameters
'''Kernel and initrd that will be used by machines'''
OXA_XEN_SERVER_KERNEL="/boot/vmlinuz-2.6.32-5-xen-amd64"
OXA_XEN_SERVER_INITRD="/boot/initrd.img-2.6.32-5-xen-amd64"
OXA_KVM_SERVER_KERNEL="/boot/vmlinuz-2.6.32-5-xen-amd64"
OXA_KVM_SERVER_INITRD="/boot/initrd.img-2.6.32-5-xen-amd64"

'''Debian-family usual file locations'''
OXA_DEBIAN_INTERFACES_FILE_LOCATION = "/etc/network/interfaces"
OXA_DEBIAN_UDEV_FILE_LOCATION = "/etc/udev/rules.d/70-persistent-net.rules"
OXA_DEBIAN_HOSTNAME_FILE_LOCATION="/etc/hostname"
OXA_DEBIAN_HOSTS_FILE_LOCATION="/etc/hosts"
OXA_DEBIAN_SECURITY_ACCESS_FILE_LOCATION="/etc/security/access.conf"

'''RedHat-family usual file locations'''
OXA_REDHAT_INTERFACES_FILE_LOCATION = "/etc/sysconfig/network-scripts/"
OXA_REDHAT_UDEV_FILE_LOCATION = "/etc/udev/rules.d/70-persistent-net.rules"
OXA_REDHAT_HOSTNAME_FILE_LOCATION="/etc/hostname"
