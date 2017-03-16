from django.core.urlresolvers import resolve

def appname(request):
	return {'appname': resolve(request.path).app_name}
