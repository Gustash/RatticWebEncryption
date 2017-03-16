from cred.models import CredTemp, Cred, State
from django.utils import timezone
import email
import imaplib
import logging

IMAP_SERVER = 'imap.gmail.com'
IMAP_USER = 'testdjango88@gmail.com'
IMAP_PASS = 'django123'

logger = logging.getLogger(__name__)

class Message:
	def __init__(self, mail_id, message_id):
		self.mail_id = mail_id
		self.message_id = message_id
		self.reply_to_id = None

	def find_reply(self):
		mail = imaplib.IMAP4_SSL(IMAP_SERVER)
		mail.login(IMAP_USER, IMAP_PASS)
		
		mail.select('[Gmail]/Todo o correio')

		retcode, messages = mail.search(None, 'ALL')
		if retcode == 'OK':
			for message in messages[0].split(' '):
				if message == self.mail_id:
					if message != '':
						result, reply = mail.fetch(message, '(BODY[HEADER.FIELDS (IN-REPLY-TO)])')
						reply_id = Message.get_message_code_id(reply[0][1])
						self.reply_to_id = reply_id
						break 

	def is_reply(self):
		return len(self.reply_to_id) != 1

	def get_password(self, messages=None):
		if not self.is_reply():
			body = self.get_body()
			for line in body.split('\n'):
				if 'Password' in line:
					return line[len('Password: '):]
		elif messages != None:
			for m in messages:
				if not m.is_reply() and m.message_id == self.reply_to_id:
					return m.get_password()
		return None

	def get_user(self, messages=None):
		if not self.is_reply():
			body = self.get_body()
			for line in body.split('\n'):
				if 'User' in line:
					return line[len('User: '):]
		elif messages != None:
			for m in messages:
				if not m.is_reply() and m.message_id == self.reply_to_id:
					return m.get_user()
		return None

	def get_ct_id(self, messages=None):
		if not self.is_reply():
			body = self.get_body()
			for line in body.split('\n'):
				if 'PT_ID' in line:
					return line[len('PT_ID: '):]
				elif 'pt_id' in line:
					return line[len('pt_id: '):]
		elif messages != None:
			for m in messages:
				if not m.is_reply() and m.message_id == self.reply_to_id:
					return m.get_ct_id()
		return None

	def get_reply_body(self):
		if self.is_reply():
			mail = imaplib.IMAP4_SSL(IMAP_SERVER)
                	mail.login(IMAP_USER, IMAP_PASS)

                	mail.select('[Gmail]/Todo o correio')

                	retcode, messages = mail.search(None, 'ALL')
                	if retcode == 'OK':
                        	for message in messages[0].split(' '):
                                	if message == self.mail_id:
                                        	if message != '':
                                                	result, data = mail.uid('search', None, '(HEADER Message-ID "' + self.message_id + '")')
                                                	result, data = mail.uid('fetch', data[0].split()[-1], '(RFC822)')
                                                	email_message = email.message_from_string(data[0][1])
                                                	if email_message.is_multipart():
                                                        	body = email_message.get_payload(0).get_payload().split('\n')[0].strip()
                                                        	return body.lower()
                                                	else:
                                                        	return email_message.get_payload()


	def get_body(self):
		mail = imaplib.IMAP4_SSL(IMAP_SERVER)
		mail.login(IMAP_USER, IMAP_PASS)
		
		mail.select('[Gmail]/Todo o correio')

		retcode, messages = mail.search(None, 'ALL')
		if retcode == 'OK':
			for message in messages[0].split(' '):
				if message == self.mail_id:
					if message != '':
						result, data = mail.uid('search', None, '(HEADER Message-ID "' + self.message_id + '")')
						result, data = mail.uid('fetch', data[0].split()[-1], '(RFC822)')
						email_message = email.message_from_string(data[0][1])
						if email_message.is_multipart():
							body = email_message.get_payload(0).get_payload().split('\n')[2].strip()
							return body.lower()
						else: 
							return email_message.get_payload()
		return ''

	@staticmethod
	def get_message_code_id(message):
		start = message.find('<')  + 1
		end = message.find('>')
		return message[start:end]

class mail_manager:
	@staticmethod
	def update():
		mail = imaplib.IMAP4_SSL(IMAP_SERVER)
		mail.login(IMAP_USER, IMAP_PASS)
		
		mail.select('[Gmail]/Todo o correio')
		
		mess_unseen = []
		mess_seen = []

		retcode, messages = mail.search(None, '(UNSEEN)')
		if retcode == 'OK':
			for message in messages[0].split(' '):
				if message != '':
					result, data = mail.fetch(message, '(BODY[HEADER.FIELDS (Message-ID)])')
					message_id = Message.get_message_code_id(data[0][1])
					mess_unseen.append(Message(message, message_id))

		retcode, messages = mail.search(None, 'all')
		if retcode == 'OK':
			for message in messages[0].split(' '):
				if message != '':
					result, data = mail.fetch(message, '(BODY[HEADER.FIELDS (Message-ID)])')
					message_id = Message.get_message_code_id(data[0][1])
					mess_seen.append(Message(message, message_id))

		mail.close()

		for m in mess_seen:
			m.find_reply()

		for m in mess_unseen:
			m.find_reply()

		for m in mess_unseen:
			if m.is_reply():
				cred_temp = CredTemp.objects.get(id=int(m.get_ct_id(mess_seen)))
				if cred_temp.state == State.PENDING.value:
					if 'yes' in m.get_reply_body():
						cred_temp.state = State.GRANTED.value
						cred_temp.date_granted = timezone.now()
						cred_temp.date_expired = timezone.now() + timezone.timedelta(days=1)
					elif 'no' in m.get_reply_body():
						cred_temp.state = State.REFUSED.value
					cred_temp.save()
