from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from cred.models import CredTemp, Cred, State
from forms import CredTempForm
from django.core.urlresolvers import reverse
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class DataCred:
	def __init__(self, cred, cred_temp):
		self.cred = cred
		self.cred_temp = cred_temp

@login_required
def index(request):
        if not request.user.is_staff:
	    temp_creds = CredTemp.objects.filter(user=request.user) 
        else:
            temp_creds = CredTemp.objects.all()
        request_creds = Cred.objects.filter(id__in=temp_creds.values_list('cred_id', flat=True))
            
	data_cred = []

	for ct in temp_creds:
		for c in request_creds:
			if ct.cred_id == c.id and not c.is_deleted:
				data_cred.append(DataCred(c, ct))
	
	viewContext = {
	'title': 'Request',
	'data': data_cred 
	}
	return render(request, 'request.html', viewContext)

@login_required
def add(request):
	logger.info(request.method)
	if request.method == "POST":
		cred_temp = CredTemp(user=request.user)
		form = CredTempForm(request.user, request.POST, instance=cred_temp)
		if form.is_valid():
                        if not CredTemp.objects.filter(user=request.user, cred=request.POST.get('cred')):
 			    form.save()
			    return HttpResponseRedirect(reverse('request.views.index'))
	else:
		form = CredTempForm(requser=request.user)
		logger.info(form.is_valid())
	return render(request, 'makeRequest.html', {'form': form})

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
