from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from cred.models import CredTemp, Cred, State
from forms import CredTempForm
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _
from django.core.mail import EmailMultiAlternatives 
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from staff.decorators import rattic_staff_required

import poplib
import imaplib
import logging
import threading

logger = logging.getLogger(__name__)

class DataCred:
    def __init__(self, cred, cred_temp):
        self.cred = cred
        self.cred_temp = cred_temp

@login_required
def index(request, cfilter='special', value='all', sortdir='descending', sort='created', page=1):
    viewdict = {
            'title': _('My requests'),
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

@rattic_staff_required
def all(request, cfilter='special', value='all', sortdir='descending', sort='created', page=1):
    viewdict = {
            'title': _('Manage requests'),
            'alerts': [],
            'filter': unicode(cfilter).lower(),
            'value': unicode(value).lower(),
            'sort': unicode(sort).lower(),
            'sortdir': unicode(sortdir).lower(),
            'page': unicode(page).lower(),
            'groups': request.user.groups,
        }
    
    temp_creds = CredTemp.objects.search(request.user, owned=True, cfilter=cfilter, value=value, sortdir=sortdir, sort=sort)
    
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
    
    return render(request, 'request_all.html', viewdict)

@login_required
def add(request):
    logger.info(reverse('request.views.index'))
    if request.method == "POST":
        cred_temp = CredTemp(user=request.user)
        form = CredTempForm(request.user, request.POST, instance=cred_temp)
        if form.is_valid():
            if not CredTemp.objects.filter(user=request.user, cred=request.POST.get('cred')):
                form.save()
                send_cred_mail(request, cred_temp)
                return HttpResponseRedirect(reverse('request.views.index'))
    else:
        form = CredTempForm(requser=request.user)
    return render(request, 'request_edit.html', {'form': form})

@login_required
def bulkcancel(request):
    tocancel = CredTemp.objects.filter(id__in=request.POST.getlist('credcheck')).exclude(Q(state__gt=State.PENDING.value) & Q(state__gt=State.GRANTED.value))
    for ct in tocancel:
        ct.state = State.EXPIRED.value
        ct.date_expired = timezone.now()
        ct.save()

    return HttpResponseRedirect(reverse('request.views.index'))

@login_required
def bulkretry(request):
    toretry = CredTemp.objects.filter(id__in=request.POST.getlist('credcheck'))
    for ct in toretry:
        if ct.state != State.PENDING.value and ct.state != State.GRANTED.value:
            ct.state = State.PENDING.value
            ct.date_expired = None
            ct.save()
        send_cred_mail(request, ct)

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

@login_required
def search(request):
    return render(request, 'request_search.html', {})

def send_cred_mail(request, cred_temp):
    t = threading.Thread(target=send_thread, args=(request, cred_temp))
    t.start()

def send_thread(request, cred_temp):
    #Get all 'staff' users
    users = User.objects.filter(is_staff=True)
    #Remove all users that do not belong to the cred_temp's group
    for u in users: #Foreach user
        #Check if cred_temp's group is not in user's group list
        if not u.has_perm("auth.is_owner_{0}".format(cred_temp.cred.group_id)):
            #Remove the user from users list
            users = users.exclude(id=u.id)
    #All emails
    mails = []
    #Foreach user
    for u in users:
        #Get users email
        mails.append(u.email)   
    
    #Create the subject of the mail
    subject = 'Password requested by ' + str(request.user)
    #Get the full link to the 'cred' to which privilege is being requested
    cred_link = "http://" + request.get_host() + reverse('cred.views.detail', kwargs={'cred_id':cred_temp.cred_id}) 
    #Get the full link to the newly created 'cred_temp'
    cred_temp_link = "http://" + request.get_host() + reverse('request.views.detail', kwargs={'cred_temp_id':cred_temp.id})
    #Get the full link to the user which is requesting the privilege
    user_link = "http://" + request.get_host() + reverse('staff.views.userdetail', kwargs={'uid':cred_temp.user_id})
    #Generate html content for the mail
    html_content = render_to_string('request_mail.html', {'user':str(request.user), 'title':str(cred_temp.cred), 'user_link':user_link,'cred_temp_link':cred_temp_link, 'cred_link':cred_link, 'temp_id':str(cred_temp.id), 'description': cred_temp.description})
    #Generate the message with 'html tags' aplied
    text_content = strip_tags(html_content)

    #Send the email
    msg = EmailMultiAlternatives(subject, text_content, 'testdjango88@gmail.com', mails)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
