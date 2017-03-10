from django.forms import ModelForm, SelectMultiple, ModelMultipleChoiceField
from cred.models import CredTemp, Group, Cred
from django.db.models import Q
from cred.models import State
import logging

logger = logging.getLogger(__name__)

class CredTempForm(ModelForm):
        #cred = ModelMultipleChoiceField(widget=SelectMultiple(attrs={'class': 'rattic-tag-selector'}), queryset=Cred.objects.filter(Q(latest=None) & Q(is_deleted=False)))
    
	def __init__(self, requser = None, *args, **kwargs):
		super(CredTempForm, self).__init__(*args, **kwargs)
		self.fields['cred'].label = 'Password'
		logger.info("requser = " + str(requser))
		#existing_temp_creds = CredTemp.objects.filter(user=requser).values_list('id', flat=True)
		existing_temp_creds = CredTemp.objects.filter(user=requser).values_list('cred_id', flat=True)
		available_creds = Cred.objects.filter(Q(latest=None) & Q(is_deleted=False)).exclude(Q(id__in=existing_temp_creds))
                
		#self.fields['cred'].queryset = Cred.objects.filter(Q(state!=0) & Q(latest=None) & Q(is_deleted=False))
		self.fields['cred'].queryset = available_creds

	class Meta:
		model = CredTemp
                fields = ('cred', 'description')
                exclude = ('user', 'date_granted', 'date_expired', 'state')
		widgets = {
			#'cred': SelectMultiple(attrs={'class': 'rattic-tag-selector'}),
		}
