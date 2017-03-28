from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django import forms
from importloaders import keepass
from keepassdb.exc import AuthenticationError, InvalidDatabase
from cred.models import CredAudit
#from datetime import datetime
from django.db import models
from django.utils import timezone
from django.forms import SelectMultiple
import logging

logger = logging.getLogger(__name__)

class AuditFilterForm(forms.Form):
    hide = forms.MultipleChoiceField(
        choices=CredAudit.CREDAUDITCHOICES,
        widget=forms.SelectMultiple(attrs={'class': 'selectize-multiple'}),
        initial=[],
    )


class UserForm(forms.ModelForm):
    # We want two password input boxes
    newpass = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'btn-password-visibility'}),
        required=False,
        max_length=32,
        min_length=8
    )
    confirmpass = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        max_length=32,
        min_length=8
    )

    field = models.ForeignKey('Group', related_name='self_group', on_delete=models.CASCADE, editable=False, default=0)
    field.contribute_to_class(User, 'self_group')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        
        self_groups = Group.objects.filter(id__in=[x.self_group_id for x in User.objects.filter()])

        self.fields['email'].required = True
        self.fields['groups'].queryset = Group.objects.exclude(id__in=self_groups)

    # Define our model
    class Meta:
        model = User
        fields = ('username', 'email', 'is_active', 'is_staff', 'groups')
        widgets = {
            'groups': forms.SelectMultiple(attrs={'class': 'rattic-group-selector'}),
        }

    def clean(self):
        # Check the passwords given match
        cleaned_data = super(UserForm, self).clean()
        newpass = cleaned_data.get("newpass")
        confirmpass = cleaned_data.get("confirmpass")

        if newpass != confirmpass:
            msg = _('Passwords do not match')
            self._errors['confirmpass'] = self.error_class([msg])
            del cleaned_data['newpass']
            del cleaned_data['confirmpass']

        return cleaned_data

class GroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
	#Get all users
        users_in_group = User.objects.all()
	
	#Foreach user, check if 'this' group is in his 'group' list
	#if not, remove him from the 'user_in_group' list
        for u in User.objects.all():
            if not self.instance in u.groups.all():
                users_in_group = users_in_group.exclude(id=u.id)

	#Create a new field 'users' so that users can be added to the group when it is created or edited
        self.fields['users'] = forms.ModelMultipleChoiceField(
                label='Users', 		#Label for the 'input' is 'Users'
                required=False, 	#It is not required
                widget=SelectMultiple(attrs={'class': 'rattic-group-selector'}), 	#Set input of type 'SelectMultiple' so that multiple users can be added to the group
                queryset=User.objects.all(), 	#Set the users that can be added (all users)
                initial=users_in_group		#The initial value are those users who where already there
        )
	
	#Owners of the group are those who have permition to edit the group
        owners = None
	#Check if the group has 'id' (if it does not have an 'id', it means that the group is being created, by this time, the group have no 'id')
        if self.instance.id:
	    #
            owners = User.objects.all()
            for user in User.objects.all():
                if not user.has_perm("auth.is_owner_" + str(self.instance.id)):
                    owners = owners.exclude(id=user.id)

        self.fields['owners'] = forms.ModelMultipleChoiceField(
            queryset=User.objects.exclude(is_staff=False),
            widget=forms.SelectMultiple(attrs={'class': 'rattic-group-selector'}),
            label = _('Owners'),
	    required = True,
	    initial = owners
        )

    # Extend the Group model by adding a created column to save the date the Group was created at
    if not hasattr(Group, 'created'):
        field = models.DateTimeField(Group, auto_now_add=True)
        field.contribute_to_class(Group, 'created')

    def clean_name(self):
        if (self.cleaned_data['name']):
            if (self.cleaned_data['name'].startswith('private_')):
                raise ValidationError('Group name cannot start with "private_"')
        return self.cleaned_data['name']

    class Meta:
        model = Group
        fields = ('name',)

class KeepassImportForm(forms.Form):
    file = forms.FileField()
    password = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(attrs={'class': 'btn-password-visibility'})
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        widget=forms.Select(attrs={'class': 'rattic-group-selector'}),
    )

    def __init__(self, requser, *args, **kwargs):
        super(KeepassImportForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = Group.objects.filter(user=requser)

    def clean(self):
        cleaned_data = super(KeepassImportForm, self).clean()

        try:
            db = keepass(cleaned_data['file'], cleaned_data['password'])
            cleaned_data['db'] = db
        except AuthenticationError:
            msg = _('Could not read keepass file, the password you gave may not be correct.')
            self._errors['file'] = self.error_class([msg])
            del cleaned_data['file']
            del cleaned_data['password']
        except InvalidDatabase:
            msg = _('That file does not appear to be a valid KeePass file.')
            self._errors['file'] = self.error_class([msg])
            del cleaned_data['file']
            del cleaned_data['password']

        return cleaned_data
