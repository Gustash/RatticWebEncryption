from django.forms import ModelForm, Select
from cred.models import CredTemp, Cred
from django.db.models import Q
from django import forms
import logging

logger = logging.getLogger(__name__)

class CredTempForm(ModelForm):
	def __init__(self, requser = None, *args, **kwargs):
		super(CredTempForm, self).__init__(*args, **kwargs)
		self.fields['cred'].label = 'Password'
		logger.info("requser = " + str(requser))
		existing_temp_creds = CredTemp.objects.filter(user=requser).values_list('cred_id', flat=True)
		available_creds = Cred.objects.filter(Q(latest=None) & Q(is_deleted=False)).exclude(Q(id__in=existing_temp_creds))
                
		self.fields['cred'].queryset = available_creds

        def clean_description(self):
        	description = self.cleaned_data.get('description')
		if description.isspace():
                	raise forms.ValidationError('Description must not be blank')
		return description

	class Meta:
		model = CredTemp
                fields = ('cred', 'description')
                exclude = ('user', 'date_granted', 'date_expired', 'state')
		widgets = {
			'cred': Select(attrs={'class': 'rattic-tag-selector'}),
		}
