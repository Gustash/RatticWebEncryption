from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^list', views.index, name='index'),
	url(r'^add', views.add, name='add'),
	url(r'^c', views.bulkcancel, name='bulkcancel'),
	url(r'^r', views.bulkretry, name='bulkretry'),
	url(r'^detail/(?P<cred_temp_id>\d+)/$', views.detail, name='cred_temp_id'),
]
