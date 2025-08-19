import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
import os
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from .models import SupplierResponse, User

logger = logging.getLogger(__name__)

class EmailFetcher:
    '''Забирает и обрабатывает ответы поставщиков с сервера IMAP.
    Обслуживает подключение к почтовому серверу, получение непрочитанных писем, 
    извлечение релевантной информации и сохранение ответов поставщиков в базе данных.'''
    def __init__(self):
        self.mail = None
        self.connect()

    def connect(self):
        '''Устанавливает соединение с почтовым сервером IMAP, используя заданные настройки.'''
        try:
            if settings.EMAIL_RESPONSE_USE_SSL:
                self.mail = imaplib.IMAP4_SSL(
                    settings.EMAIL_RESPONSE_HOST, 
                    settings.EMAIL_RESPONSE_PORT
                )
            else:
                self.mail = imaplib.IMAP4(
                    settings.EMAIL_RESPONSE_HOST, 
                    settings.EMAIL_RESPONSE_PORT
                )
            
            self.mail.login(
                settings.EMAIL_RESPONSE_USER, 
                settings.EMAIL_RESPONSE_PASSWORD
            )
            return True
        except Exception as e:
            logger.error(f"Email connection failed: {e}")
            return False

    def fetch_emails(self):
        '''Извлекает непрочитанные письма из почтового ящика и обрабатывает каждое как ответ поставщика.'''
        if not self.mail:
            if not self.connect():
                return False

        try:
            self.mail.select('inbox')
            status, messages = self.mail.search(None, 'UNSEEN')
            if status != 'OK':
                logger.error("No messages found")
                return False

            for mail_id in messages[0].split():
                try:
                    status, data = self.mail.fetch(mail_id, '(RFC822)')
                    if status != 'OK':
                        continue

                    msg = email.message_from_bytes(data[0][1])
                    self.process_message(msg)
                    self.mail.store(mail_id, '+FLAGS', '\\Seen')
                except Exception as e:
                    logger.error(f"Error processing email {mail_id}: {e}")

            return True
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return False
        finally:
            self.mail.close()
            self.mail.logout()
            self.mail = None

    def process_message(self, msg):
        '''Обрабатывает отдельное письмо, извлекая данные и сохраняя ответ поставщика в базу данных.'''
        subject = self.decode_header(msg.get('Subject'))
        if not subject:
            return

        # Парсим тему письма по шаблону
        # pattern = r'Re:Request for Delivery of (.+?) \((\d+)-([\w\.]+)\)'
        # pattern = r'Re:\s*Request\s+for\s+Delivery\s+of\s+(.+?)\s*\((\d+)-([\w\.-]+)\)'
        pattern = r'Re:\s*Request\s+for\s+Delivery\s+of\s+(.+?)\s*\(\s*(\d+)\s*-\s*([\w\.-]+)\s*\)'
        match = re.search(pattern, subject)
        if not match:
            return

        product = match.group(1).strip()
        user_id = int(match.group(2))
        email_part = match.group(3)

        # Получаем email отправителя
        from_email = self.get_email_from_header(msg.get('From'))

        # Получаем дату письма
        date_tuple = email.utils.parsedate_tz(msg.get('Date'))
        if date_tuple:
            email_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        else:
            email_date = datetime.now()

        # Получаем текст письма
        body = self.get_email_body(msg)

        # Получаем вложения
        attachments = self.get_attachments(msg)

        # Сохраняем в базу
        try:
            user = User.objects.get(id=user_id)
            response = SupplierResponse.objects.create(
                user=user,
                product=product,
                email=from_email,
                subject=subject,
                message=body,
                date=email_date
            )

            # Сохраняем первое вложение
            if attachments:
                filename, content = attachments[0]
                response.attachment.save(filename, ContentFile(content))
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
        except Exception as e:
            logger.error(f"Error saving response: {e}")

    def decode_header(self, header):
        '''Декодирует буквы заголовка в формате UTF-8.'''
        if not header:
            return ""
        try:
            decoded = decode_header(header)
            return ''.join(
                [t[0].decode(t[1] or 'utf-8') if isinstance(t[0], bytes) else t[0]] 
                for t in decoded
            )
        except:
            return header

    def get_email_from_header(self, header):
        '''Извлекает email-адрес из заголовка письма.'''
        # Извлекаем email из строки вида "Имя <email@domain.com>"
        match = re.search(r'<([^>]+)>', header)
        if match:
            return match.group(1)
        return header

    def get_email_body(self, msg):
        '''Извлекает текстовое содержимое письма из объекта email-сообщения.'''
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" not in content_disposition and content_type == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return msg.get_payload(decode=True).decode()
        return ""

    def get_attachments(self, msg):
        '''Извлекает вложения из объекта email-сообщения.'''
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename:
                    filename = self.decode_header(filename)
                    attachments.append((filename, part.get_payload(decode=True)))
        return attachments
