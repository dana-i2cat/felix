'''
Created on Dec 17, 2014

@author: j.fujimoto
'''

from datetime import datetime

# django
from django import forms

# expedient
from expedient.common.utils.plugins.pluginloader import PluginLoader as PLUGINLOADER

class MonitorSDNForm(forms.Form):

    metric = forms.ChoiceField(
        choices=[('status','status'), ('bps','bps')],
        label='Metric:'
    )

    datefrom = forms.CharField(
        label='Date range:'
    )

    dateto = forms.CharField(
        label='to:'
    )

    timezone = forms.ChoiceField(
        choices=[('WET', 'GMT+0000 (WET)'), ('CET', 'GMT+0100 (CET)'), ('EET', 'GMT+0200 (EET)'), ('Asia/Tokyo', 'GMT+0900 (JST)')],
        label='Timezone:'
    )

    limit = forms.ChoiceField(
        choices=[('10', 10), ('100', 100), ('1000', 1000)],
        label='Show:'
    )

    def clean(self):
        cleaned_data = super(MonitorSDNForm, self).clean()
        # do your custom validations / transformations here
        # and some more
        print 'cleaned_data=%s' % str(cleaned_data)
        datefrom = cleaned_data.get('datefrom')
        dateto = cleaned_data.get('dateto')
        if datefrom == None or dateto == None:
            raise forms.ValidationError('Date range is not valid.')

        if datetime.strptime(datefrom, '%Y/%m/%d %H:%M') > datetime.strptime(dateto, '%Y/%m/%d %H:%M'):
            raise forms.ValidationError('Date range is not valid.')

        return cleaned_data

    def set_fields(self, settings):

        # metric
        metrics = []
        for sdn_metric in settings.get('monitoring_sdn_metric'):
            metric = [sdn_metric[0], sdn_metric[1]]
            metrics.append(metric)
        self.fields['metric'].choices = metrics

        # timezone
        timezones = []
        for m_timezone in settings.get('monitoring_timezone'):
            timezone = [m_timezone[0], m_timezone[1]]
            timezones.append(timezone)
        self.fields['timezone'].choices = timezones

        # show
        shows = []
        for m_show in settings.get('monitoring_show'):
            show = [m_show, m_show]
            shows.append(show)
        self.fields['limit'].choices = shows

        return

class MonitorCPForm(forms.Form):

    metric = forms.ChoiceField(
        choices=[('status','Status'), ('load','CPU Load')],
        label='Metric:'
    )

    datefrom = forms.CharField(
        label='Date range:'
    )

    dateto = forms.CharField(
        label='to:'
    )

    timezone = forms.ChoiceField(
        choices=[('WET', 'GMT+0000 (WET)'), ('CET', 'GMT+0100 (CET)'), ('EET', 'GMT+0200 (EET)'), ('Asia/Tokyo', 'GMT+0900 (JST)')],
        label='Timezone:'
    )

    limit = forms.ChoiceField(
        choices=[('10', 10), ('100', 100), ('1000', 1000)],
        label='Show:'
    )

    def clean(self):
        cleaned_data = super(MonitorCPForm, self).clean()
        # do your custom validations / transformations here
        # and some more
        datefrom = cleaned_data.get('datefrom')
        dateto = cleaned_data.get('dateto')
        if datefrom == None or dateto == None:
            raise forms.ValidationError('Date range is not valid.')

        if datetime.strptime(datefrom, '%Y/%m/%d %H:%M') > datetime.strptime(dateto, '%Y/%m/%d %H:%M'):
            raise forms.ValidationError('Date range is not valid.')

        return cleaned_data

    def set_fields(self, settings):

        # metric
        metrics = []
        for cp_metric in settings.get('monitoring_cp_metric'):
            metric = [cp_metric[0], cp_metric[1]]
            metrics.append(metric)
        self.fields['metric'].choices = metrics

        # timezone
        timezones = []
        for m_timezone in settings.get('monitoring_timezone'):
            timezone = [m_timezone[0], m_timezone[1]]
            timezones.append(timezone)
        self.fields['timezone'].choices = timezones

        # show
        shows = []
        for m_show in settings.get('monitoring_show'):
            show = [m_show, m_show]
            shows.append(show)
        self.fields['limit'].choices = shows

        return

class MonitorSEForm(forms.Form):

    metric = forms.ChoiceField(
        choices=[('status','status'), ('bps','bps')],
        label='Metric:'
    )

    datefrom = forms.CharField(
        label='Date range:'
    )

    dateto = forms.CharField(
        label='to:'
    )

    timezone = forms.ChoiceField(
        choices=[('WET', 'GMT+0000 (WET)'), ('CET', 'GMT+0100 (CET)'), ('EET', 'GMT+0200 (EET)'), ('Asia/Tokyo', 'GMT+0900 (JST)')],
        label='Timezone:'
    )

    limit = forms.ChoiceField(
        choices=[('10', 10), ('100', 100), ('1000', 1000)],
        label='Show:'
    )

    def clean(self):
        cleaned_data = super(MonitorSEForm, self).clean()
        # do your custom validations / transformations here
        # and some more
        datefrom = cleaned_data.get('datefrom')
        dateto = cleaned_data.get('dateto')
        if datefrom == None or dateto == None:
            raise forms.ValidationError('Date range is not valid.')

        if datetime.strptime(datefrom, '%Y/%m/%d %H:%M') > datetime.strptime(dateto, '%Y/%m/%d %H:%M'):
            raise forms.ValidationError('Date range is not valid.')

        return cleaned_data

    def set_fields(self, settings):

        # metric
        metrics = []
        for se_metric in settings.get('monitoring_se_metric'):
            metric = [se_metric[0], se_metric[1]]
            metrics.append(metric)
        self.fields['metric'].choices = metrics

        # timezone
        timezones = []
        for m_timezone in settings.get('monitoring_timezone'):
            timezone = [m_timezone[0], m_timezone[1]]
            timezones.append(timezone)
        self.fields['timezone'].choices = timezones

        # show
        shows = []
        for m_show in settings.get('monitoring_show'):
            show = [m_show, m_show]
            shows.append(show)
        self.fields['limit'].choices = shows

        return
