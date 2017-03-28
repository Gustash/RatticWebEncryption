from cred.models import CredTemp, State
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)

import email
import imaplib

IMAP_SERVER = 'imap.gmail.com'
IMAP_USER = 'testdjango88@gmail.com'
IMAP_PASS = 'django123'

class Message:
    answer = None
    cred_temp_id = None
    mail = None
    reply_num_id = None
    num_id = None

    def __init__(self, mail, id):
        self.mail = mail
        self._find_self_id(id)
        self.num_id = id
        if self._is_reply(id):
            if self._get_answer(id):
                self._get_reply(id)
	
    def _find_self_id(self, id):
        result, data = self.mail.fetch(id, '(BODY[HEADER.FIELDS (Message-ID)])')
        self.self_id = self._get_message_code(data[0][1])

    def _is_reply(self, id):
		# If the header has reply-id, save id and return True
		# Else, return False
        result, data = self.mail.fetch(id, '(BODY[HEADER.FIELDS (IN-REPLY-TO)])')
        if data[0]:
            if data[0][1]:
                self.reply_message_id = self._get_message_code(data[0][1])
                return True
        return False

    def _get_message_code(self, raw_id):
        start = raw_id.find('<') + 1
        end = raw_id.find('>')
        return raw_id[start:end]


    def _get_html_text(self, html_text):
        while '<' in html_text and '>' in html_text:
            html_text = html_text[:html_text.find('<')] + html_text[html_text.find('>') + 1:]
        return html_text
                         
    def _get_answer(self, id):
        body = self._get_body(self.self_id, True)
        if 'yes' in body:
            self.answer = 'yes'
            return True
        elif 'no' in body:
            self.answer = 'no'
            return True
        return False

    def _get_body(self, id, is_reply):
        result, data = self.mail.uid('search', None, '(HEADER Message-ID "'+id+'")')
        self.reply_num_id = data[0].split()[-1]
        result, data = self.mail.uid('fetch', self.reply_num_id, '(RFC822)')
        if data[0]:
            if data[0][1]:
                email_message = email.message_from_string(data[0][1])
                if email_message.is_multipart():
                    if is_reply:
                        return email_message.get_payload(0).get_payload().split('\n')[0].strip().lower()
                    else:
                        return email_message.get_payload(0).get_payload().split('\n')[2].strip().lower()
                else:
                    return self._get_html_text(email_message.get_payload().lower())
        return None


    def _get_reply(self, id):
        body = self._get_body(self.reply_message_id, False)
        if body:
            for line in body.split('\n'):
                if 'pt_id' in line:
                    self.cred_temp_id = line[len('pt_id: '):]
                    return True
        return False
	
    def update_cred_temp(self):
        if self.answer:
            if self.cred_temp_id:
                cred_temp = CredTemp.objects.get(id=self.cred_temp_id)
                self._clean_mailbox()
                if cred_temp.state == State.PENDING.value:
                    if 'yes' in self.answer: 
                        cred_temp.state = State.GRANTED.value
                        cred_temp.date_granted = timezone.now()
                        cred_temp.date_expired = timezone.now() + timezone.timedelta(days=1)
                        cred_temp.save()
                        return True
                    else:
                        cred_temp.state = State.REFUSED.value
                        cred_temp.save()
                        return True
        return False

    def _clean_mailbox(self):
        self.mail.store("1:{0}".format(self.num_id), '+X-GM-LABELS', '\\Trash')
        self.mail.store("1:{0}".format(self.reply_num_id), '+X-GM-LABELS', '\\Trash')
		
        self.mail.select('[Gmail]/Caixote do Lixo')
        self.mail.store("1:*", '+FLAGS', '\\Deleted')

class MailManager:
    @staticmethod
    def update():
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASS)

        mail.select('[Gmail]/Todo o correio')

        retcode, messages = mail.search(None, '(UNSEEN)')
        if retcode == 'OK':
            for message in messages[0].split(' '):
                if message != '':
                    Message(mail, message).update_cred_temp()
        mail.expunge()
        mail.close()
