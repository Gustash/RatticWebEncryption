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
from email import parser
import poplib
import logging

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

	read_mail()

        temp_creds = CredTemp.objects.search(request.user, cfilter=cfilter, value=value, sortdir=sortdir, sort=sort)
	
	# Apply the sorting rules
	if sortdir == 'ascending':
        	viewdict['revsortdir'] = 'descending'
    	elif sortdir == 'descending':
        	viewdict['revsortdir'] = 'ascending'
    	else:
		raise Http404

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
	logger.info(request.method)
	if request.method == "POST":
		cred_temp = CredTemp(user=request.user)
		form = CredTempForm(request.user, request.POST, instance=cred_temp)
		if form.is_valid():
                        if not CredTemp.objects.filter(user=request.user, cred=request.POST.get('cred')):
 			   form.save()
			   subject = 'Password requested by ' + str(request.user)
		    	   message = 'New request made by \'' + str(request.user) + '\' to access \'' + str(Cred.objects.get(id=cred_temp.cred_id)) + '\'\nDescription: ' + str(cred_temp.description)
			   send_mail(subject, message, 'testdjango@gmail.com', ['vadimz2@hotmail.com'])
			   return HttpResponseRedirect(reverse('request.views.index'))
	else:
		form = CredTempForm(requser=request.user)
		logger.info(form.is_valid())
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
 	subject = 'Password requested by ' + str(request.user)
	message = 'New request made by \'' + str(request.user) + '\' to access \'' + str(Cred.objects.get(id=ct.cred_id)) + '\'\nDescription: ' + str(ct.description)
	send_mail(subject, message, 'testdjango@gmail.com', ['vadimz2@hotmail.com'])


		

	return HttpResponseRedirect(reverse('request.views.index'))

@login_required
def detail(request, cred_temp_id):
	cred_temp = CredTemp.objects.get(id=cred_temp_id)	
	if request.user.is_staff or cred_temp.state == State.GRANTED.value:
		link = "cred.views.detail"
	else:
		link = None

	logger.info(cred_temp.description)

	viewContext = {
		'data': cred_temp,
		'link': link
	}

	return render(request, 'request_detail.html', viewContext)

def read_mail():
	pop_conn = poplib.POP3_SSL('pop.gmail.com')
	pop_conn.user('testdjango88')
	pop_conn.pass_('django123')
	
	numMessages = len(pop_conn.list()[1])
	for i in range(numMessages):
		logger.info("Reading mail...")
		for j in pop_conn.retr(i + 1)[1]:
			if j == 'YES':
				logger.info('Message Received: YES')
			elif j == 'NO':
				logger.info('Message Received: NO')
	pop_conn.quit()

	logger.info("No more emails...")
