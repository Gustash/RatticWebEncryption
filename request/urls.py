from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('request.views',
	url(r'^add', views.add, name='add'),
	url(r'^c', views.bulkcancel, name='bulkcancel'),
	url(r'^r', views.bulkretry, name='bulkretry'),
	url(r'^detail/(?P<cred_temp_id>\d+)/$', views.detail, name='cred_temp_id'),

        # New list views
        url(r'^list/$', 'index', name='index'),
        url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/$', 'index', name='index'),
        url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/$', 'index', name='index'),
        url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/page-(?P<page>\d+)/$', 'index', name='index'),
)
