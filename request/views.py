from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from cred.models import CredTemp, Cred, State
from forms import CredTempForm
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
import poplib
import imaplib
import logging
import re
import sys
import threading

logger = logging.getLogger(__name__)

class DataCred:
	def __init__(self, cred, cred_temp):
		self.cred = cred
		self.cred_temp = cred_temp

@login_required
def index(request, cfilter='special', value='all', sortdir='descending', sort='created', page=1):
	viewdict = {
        	'title': _('All requests'),
        	'alerts': [],
        	'filter': unicode(cfilter).lower(),
        	'value': unicode(value).lower(),
	        'sort': unicode(sort).lower(),
        	'sortdir': unicode(sortdir).lower(),
	        'page': unicode(page).lower(),
        	'groups': request.user.groups,
        }
	
        temp_creds = CredTemp.objects.search(request.user, cfilter=cfilter, value=value, sortdir=sortdir, sort=sort)
	
	# Apply the sorting rules
	if sortdir == 'ascending':
        	viewdict['revsortdir'] = 'descending'
    	elif sortdir == 'descending':
        	viewdict['revsortdir'] = 'ascending'
    	else:
		raise Http404

        if cfilter == 'search':
                viewdict['title'] = _('Requests for search "%(searchstring)s"') % {'searchstring': value, }

	# Get the page
	paginator = Paginator(temp_creds, request.user.profile.items_per_page)
	try:
		temp_creds = paginator.page(page)
	except PageNotAnInteger:
		temp_creds = paginator.page(1)
	except EmptyPage:
		temp_creds = paginator.page(paginator.num_pages)

        viewdict['data'] = temp_creds
	
	return render(request, 'request_list.html', viewdict)

@login_required
def add(request):
	if request.method == "POST":
		cred_temp = CredTemp(user=request.user)
		form = CredTempForm(request.user, request.POST, instance=cred_temp)
		if form.is_valid():
                        if not CredTemp.objects.filter(user=request.user, cred=request.POST.get('cred')):
 			   form.save()
			   send_cred_mail(str(request.user), str(Cred.objects.get(id=cred_temp.cred_id)), str(cred_temp.id), cred_temp.description)
			   return HttpResponseRedirect(reverse('request.views.index'))
	else:
		form = CredTempForm(requser=request.user)
	return render(request, 'request_edit.html', {'form': form})

@login_required
def bulkcancel(request):
	tocancel = CredTemp.objects.filter(id__in=request.POST.getlist('credcheck')).exclude(state__gt=0)
	for ct in tocancel:
		ct.state = State.EXPIRED.value
		ct.date_expired = timezone.now()
		ct.save()

	return HttpResponseRedirect(reverse('request.views.index'))

@login_required
def bulkretry(request):
	toretry = CredTemp.objects.filter(id__in=request.POST.getlist('credcheck'))
	for ct in toretry:
		if ct.state != State.PENDING.value:
			ct.state = State.PENDING.value
			ct.date_expired = None
			ct.save()
		send_cred_mail(str(request.user), str(Cred.objects.get(id=ct.cred_id)), str(ct.id), ct.description)

	return HttpResponseRedirect(reverse('request.views.index'))

@login_required
def detail(request, cred_temp_id):
	cred_temp = CredTemp.objects.get(id=cred_temp_id)	
	if request.user.is_staff or cred_temp.state == State.GRANTED.value:
		link = "cred.views.detail"
	else:
		link = None

	viewContext = {
		'data': cred_temp,
		'link': link
	}

	return render(request, 'request_detail.html', viewContext)

def send_cred_mail(user, cred, cred_id, description):
	t = threading.Thread(target=send_thread, args=(user, cred, cred_id, description))
	t.start()

def send_thread(user, cred, cred_id, description):
	subject = 'Password requested by ' + user
	message = 'New request made by \'' + user + '\' to acces \'' + cred + '\'\n\nPassword: ' + cred + '\nPT_ID: ' + cred_id + '\nUser: ' + user + '\n\nDescription:\n' + description
	send_mail(subject, message, 'testdjango@gmail.com', ['vadimz2@hotmail.com'])
