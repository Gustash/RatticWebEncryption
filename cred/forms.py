from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm, SelectMultiple, Select, PasswordInput
from django.contrib.auth.models import User
import paramiko
from ssh_key import SSHKey
from models import Cred, Tag, Group
from widgets import CredAttachmentInput, CredIconChooser

from cipher import key_rsa
from cipher import AESCipher
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)

class ExportForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'btn-password-visibility'}
    ))


class TagForm(ModelForm):
    class Meta:
        model = Tag


class CredForm(ModelForm):
    def __init__(self, requser, group_id = None, *args, **kwargs):
        self.user = requser
        if (group_id is not None):
            self.group_id = group_id

        # Check if a new attachment was uploaded
        self.changed_ssh_key = len(args) > 0 and args[1].get('ssh_key', None) is not None
        self.changed_attachment = len(args) > 0 and args[1].get('attachment', None) is not None

        super(CredForm, self).__init__(*args, **kwargs)

        if self.instance.group_id not in [user.self_group_id for user in User.objects.all()]:
            self.fields['group'].widget = Select(attrs={'class': 'rattic-group-selector', 'id': 'group_selector'})
            self.fields['group'].label = _('Owner Group')

            self.fields['groups'].widget = SelectMultiple(attrs={'class': 'rattic-group-selector'})
            self.fields['groups'].label = _('Viewers Groups')
        else:
            logger.info('I am here')
            #self.fields['group'].widget = Select(attrs={'id': 'group_selector', 'style': 'display: none'})
            self.fields['group'].widget = Select(attrs={'id': 'group_selector', 'class': 'hidden-select'})
            self.fields['group'].label = ''

            self.fields['groups'].widget = SelectMultiple(attrs={'id': 'id_groups', 'class': 'hidden-select'})
            self.fields['groups'].label = ''

        # Limit the group options to groups that the user is in
        self.fields['group'].queryset = Group.objects.filter(user=requser).exclude(id__in=[u.self_group_id for u in User.objects.all()])
        self.fields['group'].required = False

        self.fields['groups'].queryset = Group.objects.exclude(id__in=[u.self_group_id for u in User.objects.all()])

        # Make the URL invalid message a bit more clear
        self.fields['url'].error_messages['invalid'] = _("Please enter a valid HTTP/HTTPS URL")

        # Check if cred already exists
        if (self.instance.id is not None):
            # Only decrypt password if it isn't a private one
            if not len(User.objects.filter(self_group=self.instance.group)) > 0:
                # Decrypt the password before you show it on the PasswordInput
                if (self.instance.id is not None):
                    mesh = AESCipher.mesh(str(self.instance.created), str(self.instance.group.created))
                    encryptor = AESCipher(mesh)
                    self.initial['password'] = encryptor.decrypt(self.instance.password)

    def is_valid(self):
        if not self.instance.created:
            self.instance.created = timezone.now()
        if not self.group_id:
            self.group_id = self.user.self_group_id
        valid = super(CredForm, self).is_valid()

        return valid

    def clean(self):
        cleaned_data = super(CredForm, self).clean()
        if not cleaned_data.get('group'):
            group = Group.objects.get(id=self.user.self_group_id)
            cleaned_data['group'] = group
        return cleaned_data

    def clean_title(self):
        self.cleaned_data['title'] = self.cleaned_data['title'].lstrip()
        if not self.cleaned_data['title']:
            msg = "Title can't be empty"
            self._errors["title"] = self.error_class([msg])
            return ''
        return self.cleaned_data['title']

    def clean_password(self):
        logger.info(self.group_id)
        if self.group_id:
            if (self.instance.id is None):
                created_date = timezone.now()
                # Save the current date in the object instance
                self.instance.created = created_date
        else:
            created_date = self.instance.created
        if self.group_id == self.user.self_group_id:
            return self.cleaned_data['password']
        else:
            # Get the date the Group was created at
            group_date = Group.objects.filter(id=self.group_id)[0].created
            # Use a mesh of the date the cred is created and the date the group was created as a key
            mesh = AESCipher.mesh(str(created_date), str(group_date))
            logger.info("Encription Mesh: " + mesh)
            password = self.cleaned_data['password']
            encryptor = AESCipher(mesh)
            return encryptor.encrypt(password)

    def save(self, *args, **kwargs):
        # Get the filename from the file object
        if self.changed_attachment:
            self.instance.attachment_name = self.cleaned_data['attachment'].name
        if self.changed_ssh_key:
            self.instance.ssh_key_name = self.cleaned_data['ssh_key'].name

        # Call save upstream to save the object
        super(CredForm, self).save(*args, **kwargs)

    def clean_ssh_key(self):
        if self.cleaned_data.get("ssh_key") is not None:
            got = self.cleaned_data['ssh_key'].read()
            self.cleaned_data['ssh_key'].seek(0)
            try:
                SSHKey(got, self.cleaned_data['password']).key_obj
            except paramiko.ssh_exception.SSHException as error:
                raise forms.ValidationError(error)
        return self.cleaned_data['ssh_key']

    class Meta:
        model = Cred
        # These field are not user configurable
        exclude = Cred.APP_SET
        widgets = {
            # Use chosen for the tag field
            'tags': SelectMultiple(attrs={'class': 'rattic-tag-selector'}),
            #'group': Select(attrs={'class': 'rattic-group-selector', 'id': 'group_selector'}),
            #'groups': SelectMultiple(attrs={'class': 'rattic-group-selector'}),
            'password': PasswordInput(render_value=True, attrs={'class': 'btn-password-generator btn-password-visibility'}),
            'ssh_key': CredAttachmentInput,
            'attachment': CredAttachmentInput,
            'iconname': CredIconChooser,
        }
