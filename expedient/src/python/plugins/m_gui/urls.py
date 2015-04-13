'''
Created on Jun 19, 2010

@author: jnaous
'''
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('m_gui.views.monitoring',
    url(r'^slice/$', 'slice_list', name='m_slice_list'),
    url(r'^slice/detail/(?P<slice_id>.*)/$', 'slice_detail', name='m_slice_detail'),
    url(r'^sdn/$', 'monitor_sdn', name='m_monitor_sdn_base'),
    url(r'^sdn/(?P<resource_id>.*)/$', 'monitor_sdn', name='m_monitor_sdn'),
    url(r'^cp/$', 'monitor_cp', name='m_monitor_cp_base'),
    url(r'^cp/(?P<resource_id>.*)/$', 'monitor_cp', name='m_monitor_cp'),
    url(r'^se/$', 'monitor_se', name='m_monitor_se_base'),
    url(r'^se/(?P<resource_id>.*)/$', 'monitor_se', name='m_monitor_se'),
)
