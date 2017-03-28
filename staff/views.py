from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views.generic.edit import UpdateView, FormView
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _
from django_otp import user_has_device, devices_for_user
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q

import os
import datetime
from django.utils.timezone import now
from django.utils.timezone import utc

from cred.icon import get_icon_list
from cred.models import CredAudit, Cred, Tag
from cred.forms import CredForm
from models import UserForm, GroupForm, KeepassImportForm, AuditFilterForm
from decorators import rattic_staff_required

import logging
import permissions

logger = logging.getLogger(__name__)

class perm_group():
    group = None
    perm = False
    def __init__(self, group, perm):
	self.group = group
	self.perm = perm

@rattic_staff_required
def home(request):
    userlist = User.objects.all()
    grouplist = Group.objects.exclude(id__in=[user.self_group_id for user in User.objects.all()])
    perm_groups = []
    for group in grouplist:
    	perm_groups.append(perm_group(group, request.user.has_perm('auth.is_owner_' + str(group.id))))

    return render(request, 'staff_home.html', {'userlist': userlist, 'grouplist': perm_groups})


@rattic_staff_required
def userdetail(request, uid):
    user = get_object_or_404(User, pk=uid)
    if settings.LDAP_ENABLED and settings.USE_LDAP_GROUPS:
        from django_auth_ldap.backend import LDAPBackend
        popuser = LDAPBackend().populate_user(user.username)
        if popuser is None:
            user.is_active = False
            user.save()
            return HttpResponseRedirect(reverse('cred.views.list',
                args=('changeadvice', user.id)))
    credlogs = CredAudit.objects.filter(user=user, cred__group__in=request.user.groups.all())[:5]
    morelink = reverse('staff.views.audit', args=('user', user.id))
    return render(request, 'staff_userdetail.html', {
        'viewuser': user,
        'credlogs': credlogs,
        'morelink': morelink,
        'hastoken': user_has_device(user)})


@rattic_staff_required
def groupadd(request):
    if request.method == 'POST':
        logger.info(request.POST)
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
        for user in request.POST.getlist('users'):
            User.objects.get(id=user).groups.add(form.instance)
            #request.user.groups.add(form.instance)
        owners = form.data.getlist('owners')
        permission = permissions.get_or_set_owner_permission(form.instance.id, form.instance.name)
        logger.info(permission)
        for user in User.objects.filter(id__in=owners):
            user.user_permissions.add(permission)
            user.save()
	    logger.info(user.has_perm('auth.is_owner_' + str(form.instance.id)))
#            request.user.groups.add(form.instance)
        return HttpResponseRedirect(reverse('staff.views.home'))
    else:
        form = GroupForm()

    return render(request, 'staff_groupedit.html', {'form': form})


@rattic_staff_required
def groupdetail(request, gid):
    is_owner = request.user.has_perm("auth.is_owner_" + gid)
    group = get_object_or_404(Group, pk=gid)
    return render(request, 'staff_groupdetail.html', {'group': group, 'is_owner': is_owner})


@rattic_staff_required
def groupedit(request, gid):
    is_owner = request.user.has_perm("auth.is_owner_" + gid)
    if not is_owner:
        return render(request, 'staff_notallowed.html')
    group = get_object_or_404(Group, pk=gid)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            group_id = form.instance.id
            group_name = form.instance.name
            permission_name = "auth.is_owner_" + str(group_id)
            permission = permissions.get_or_set_owner_permission(group_id, group_name)
            owners = form.data.getlist('owners')
            for user in User.objects.all():
                user.groups=user.groups.exclude(id=form.instance.id)
            for user_id in request.POST.getlist('users'):
                user = User.objects.get(id=user_id)
                if not user.groups.filter(id=group_id):
                    user.groups.add(form.instance)
            for owner in User.objects.filter(Q(user_permissions=permission)).distinct():
                if owner.has_perm(permission_name) and str(owner.id) not in owners:
                    owner.user_permissions.remove(permission)
                    logger.info('No longer an owner: ' + str(owner.id) + ' - ' + owner.username)
            for owner_id in owners:
                owner = User.objects.get(id=owner_id)
                if not owner.groups.filter(id=group_id):
                    owner.groups.add(group)
                if not owner.has_perm(permission_name):
                    owner.user_permissions.add(permission)
                    logger.info('New owner: ' + str(owner.id) + ' - ' + owner.username)
                
            return HttpResponseRedirect(reverse('staff.views.home'))
        else:
            group = get_object_or_404(Group, pk=gid)
    else:
        form = GroupForm(instance=group)

    return render(request, 'staff_groupedit.html', {'group': group, 'form': form})


@rattic_staff_required
def groupdelete(request, gid):
    is_owner = request.user.has_perm("auth.is_owner_" + gid)
    if not is_owner:
        return render(request, 'staff_notallowed.html')
    group = get_object_or_404(Group, pk=gid)
    if request.method == 'POST':
        group.delete()
        return HttpResponseRedirect(reverse('staff.views.home'))
    return render(request, 'staff_groupdetail.html', {'group': group, 'delete': True})


@rattic_staff_required
def userdelete(request, uid):
    user = get_object_or_404(User, pk=uid)
    if request.method == 'POST':
        try:
            group = Group.objects.get(id=user.self_group_id)
            group.delete()
        except:
            pass
        user.delete()
        return HttpResponseRedirect(reverse('staff.views.home'))
    return render(request, 'staff_userdetail.html', {'viewuser': user, 'delete': True})


@rattic_staff_required
def audit(request, by, byarg):
    auditlog = CredAudit.objects.all()
    item = None

    if by == 'user':
        item = get_object_or_404(User, pk=byarg)
        auditlog = auditlog.filter(user=item)
    elif by == 'cred':
        item = get_object_or_404(Cred, pk=byarg)
        auditlog = auditlog.filter(cred=item)
    elif by == 'days':
        item = int(byarg)
        try:
            delta = datetime.timedelta(days=int(byarg))
            datefrom = now() - delta
        except OverflowError:
            datefrom = datetime.datetime(1970, 1, 1).replace(tzinfo=utc)
        auditlog = auditlog.filter(time__gte=datefrom)

    if request.method == 'POST':
        form = AuditFilterForm(request.POST)
    else:
        form = AuditFilterForm()

    if form.is_valid():
        auditlog = auditlog.exclude(audittype__in=form.cleaned_data['hide'])

    paginator = Paginator(auditlog, request.user.profile.items_per_page)
    page = request.GET.get('page')

    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    return render(request, 'staff_audit.html', {
        'filterform': form,
        'logs': logs,
        'by': by,
        'item': item,
        'byarg': byarg
    })

@rattic_staff_required
def download(request):
    return render(request, 'account_download_key.html', {})

class NewUser(FormView):
    form_class = UserForm
    template_name = 'staff_useredit.html'
    success_url = reverse_lazy('staff.views.download')

    # Staff access only
    @method_decorator(rattic_staff_required)
    def dispatch(self, *args, **kwargs):
        return super(NewUser, self).dispatch(*args, **kwargs)

    # Create the user, set password to newpass
    def form_valid(self, form):
        if form.cleaned_data['newpass'] is not None and len(form.cleaned_data['newpass']) > 0:
            user = form.save()
            user.set_password(form.cleaned_data['newpass'])
            user.save()
            group = Group(name="private_" + str(user), created=timezone.now())
            group.save()
            user.self_group = group
            user.groups.add(group)
            user.save()
            return super(NewUser, self).form_valid(form)
        return super(NewUser, self).form_invalid(form)


class UpdateUser(UpdateView):
    model = User
    form_class = UserForm
    template_name = 'staff_useredit.html'
    success_url = reverse_lazy('staff.views.home')

    # Staff access only
    @method_decorator(rattic_staff_required)
    def dispatch(self, *args, **kwargs):
        return super(UpdateUser, self).dispatch(*args, **kwargs)

    # If the password changed, set password to newpass
    def form_valid(self, form):
        if form.cleaned_data['newpass'] is not None and len(form.cleaned_data['newpass']) > 0:
            form.instance.set_password(form.cleaned_data['newpass'])
        # If user is having groups removed we want change advice for those
        # groups
        groups = []
        for g in Group.objects.all():
            if g in form.cleaned_data['groups'] or g.id == form.instance.self_group_id:
                groups.append(g)
        form.cleaned_data['groups'] = groups
    
        if form.instance.is_active and 'groups' in form.changed_data:
            # Get a list of the missing groups
            missing_groups = []
            for g in form.instance.groups.all():
                if g not in form.cleaned_data['groups']:
                    missing_groups.append('group=' + str(g.id))

            # The user may have just added groups
            if len(missing_groups) > 0:
                self.success_url = reverse('cred.views.list',
                        args=('changeadvice', form.instance.id)) + '?' + '&'.join(missing_groups)
        # If user is becoming inactive we want to redirect to change advice
        if 'is_active' in form.changed_data and not form.instance.is_active:
            self.success_url = reverse('cred.views.list', args=('changeadvice', form.instance.id))
        return super(UpdateUser, self).form_valid(form)


@rattic_staff_required
def upload_keepass(request):
    # If data was submitted
    if request.method == 'POST':
        form = KeepassImportForm(request.user, request.POST, request.FILES)
        # And it is valid
        if form.is_valid():
            # Store the data in the session
            data = {
                'group': form.cleaned_data['group'].id,
                'entries': form.cleaned_data['db']['entries'],
            }
            request.session['imported_data'] = data

            # Start the user processing entries
            return HttpResponseRedirect(reverse('staff.views.import_overview'))
    else:
        form = KeepassImportForm(request.user)
    return render(request, 'staff_keepassimport.html', {'form': form})


@rattic_staff_required
def import_overview(request):
    # If there was no session data, return 404
    if 'imported_data' not in request.session.keys():
        raise Http404

    # Get the entries to import
    entries = request.session['imported_data']['entries']

    # If there is nothing left, go back home
    if len(entries) == 0:
        del request.session['imported_data']
        request.session.save()
        return HttpResponseRedirect(reverse('staff.views.home'))

    return render(request, 'staff_import_overview.html', {
        'entries': entries,
    })


@rattic_staff_required
def import_ignore(request, import_id):
    # If there was no session data, return 404
    if 'imported_data' not in request.session.keys():
        raise Http404

    # Get the entry we are concerned with
    try:
        del request.session['imported_data']['entries'][int(import_id)]
        request.session.save()
    except IndexError:
        raise Http404

    return HttpResponseRedirect(reverse('staff.views.import_overview'))


@rattic_staff_required
def import_process(request, import_id):
    # If there was no session data, return 404
    if 'imported_data' not in request.session.keys():
        raise Http404

    # Get the entry we are concerned with
    try:
        entry = request.session['imported_data']['entries'][int(import_id)]
    except IndexError:
        raise Http404

    # Get the group
    groupid = request.session['imported_data']['group']
    try:
        group = Group.objects.get(pk=groupid)
    except Group.DoesNotExist:
        del request.session['imported_data']
        raise Http404

    if request.method == 'POST':
        # Try and import what we have now

        # Did the user upload a new attachment
        if entry['filename'] and 'attachment' not in request.FILES.keys():
            sfile = SimpleUploadedFile(entry['filename'], bytes(entry['filecontent']))
            request.FILES['attachment'] = sfile

        # Build the form
        form = CredForm(request.user, request.POST, request.FILES)

        # Do we have enough data to save?
        if form.is_valid():

            # Save the credential
            form.save()

            # Write the audit log
            CredAudit(
                audittype=CredAudit.CREDADD,
                cred=form.instance,
                user=request.user,
            ).save()

            # Remove the entry we're importing
            del request.session['imported_data']['entries'][int(import_id)]
            request.session.save()

            # Go back to the overview
            return HttpResponseRedirect(reverse('staff.views.import_overview'))

    else:
        # Init the cred, and create the form
        processed = dict(entry)

        # Create all the tags
        tlist = []
        for t in processed['tags']:
            (tag, create) = Tag.objects.get_or_create(name=t)
            tlist.append(tag)
        processed['tags'] = tlist

        # Setup the group
        processed['group'] = group

        # If the icon is empty set it
        if 'iconname' not in processed.keys():
            processed['iconname'] = 'Key.png'

        # Remove the attachment
        if processed['filename']:
            del processed['filename']
            del processed['filecontent']

        # Create the form
        form = CredForm(request.user, processed, {})

    return render(request, 'staff_import_process.html', {
        'form': form,
        'icons': get_icon_list(),
    })


@rattic_staff_required
def credundelete(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)

    try:
        lastchange = CredAudit.objects.filter(
            cred=cred,
            audittype__in=[CredAudit.CREDCHANGE, CredAudit.CREDADD],
        ).latest().time
    except CredAudit.DoesNotExist:
        lastchange = _("Unknown (Logs deleted)")

    # Check user has perms
    if not cred.is_owned_by(request.user):
        raise Http404
    if request.method == 'POST':
        CredAudit(audittype=CredAudit.CREDADD, cred=cred, user=request.user).save()
        cred.is_deleted = False
        cred.save()
        return HttpResponseRedirect(reverse('cred.views.list', args=('special', 'trash')))

    CredAudit(audittype=CredAudit.CREDVIEW, cred=cred, user=request.user).save()

    return render(request, 'cred_detail.html', {'cred': cred, 'lastchange': lastchange, 'action': reverse('cred.views.delete', args=(cred_id,)), 'undelete': True})


@rattic_staff_required
def removetoken(request, uid):
    # Grab the user
    user = get_object_or_404(User, pk=uid)

    # Show confirm form on GET
    if request.method != 'POST':
        return render(request, 'staff_removetoken.html', {
            'user': user,
        })

    # Delete all devices (backup, token and phone)
    for dev in devices_for_user(user):
        dev.delete()

    # Redirect to the users detail page
    return HttpResponseRedirect(reverse('staff.views.userdetail', args=(uid,)))
