'''
Created on Jun 19, 2010

@author: jnaous
'''
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('m_gui.views.monitoring',
    url(r'^slice/$', 'slice_list', name='m_slice_list'),
    url(r'^slice/detail/(?P<slice_id>.*)/$', 'slice_detail', name='m_slice_detail'),
    url(r'^monitoring/sdn/$', 'monitor_sdn', name='m_monitor_sdn_base'),
    url(r'^monitoring/sdn/(?P<resource_id>.*)/$', 'monitor_sdn', name='m_monitor_sdn'),
    url(r'^monitoring/cp/$', 'monitor_cp', name='m_monitor_cp_base'),
    url(r'^monitoring/cp/(?P<resource_id>.*)/$', 'monitor_cp', name='m_monitor_cp'),
)
