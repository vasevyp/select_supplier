import re
import email
import imaplib
import logging
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile

from .models import SupplierResponse, User

logger = logging.getLogger(__name__)

def contains_key_phrase(subject):
    """Проверяет наличие ключевой фразы в теме письма без учета регистра и пунктуации."""
    if not subject:
        return False
    # Приводим к нижнему регистру и удаляем знаки препинания
    normalized_subject = re.sub(r'[^\w\s]', '', subject.lower())
    # Проверяем наличие всех ключевых слов (раздельно, но в любом порядке)
    keywords = ["request", "for", "delivery", "of"]
    # Проверяем, что все ключевые слова присутствуют
    return all(keyword in normalized_subject for keyword in keywords)

def clean_product_name(product):
    """Очищает название продукта от лишних элементов."""
    if not product:
        return ""
    # Удаляем префиксы (Re:, Fwd: и т.д.)
    prefixes = ["re:", "fwd:", "fw:"]
    for prefix in prefixes:
        if product.lower().startswith(prefix):
            product = product[len(prefix):].strip()
    # Удаляем заключенные в кавычки части
    product = re.sub(r'["\'«»].*?["\'«»]', '', product)
    # Удаляем email-подобные строки
    product = re.sub(r'\S+@\S+', '', product)
    # Удаляем лишние пробелы
    return re.sub(r'\s+', ' ', product).strip()

class EmailFetcher:
    def __init__(self):
        self.mail = None
        self.logger = logging.getLogger('customer_account.email_fetcher')
    
    def connect(self):
        try:
            self.logger.info("Connecting to IMAP server...")
            if getattr(settings, 'EMAIL_RESPONSE_USE_SSL', True):
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
            self.logger.info("Successfully connected to IMAP server")
            return True
        except Exception as e:
            self.logger.error(f"IMAP connection failed: {str(e)}")
            return False
    
    def fetch_emails(self):
        try:
            # Проверка соединения
            try:
                self.mail.noop()
            except Exception as e:
                self.logger.warning(f"Connection lost ({str(e)}), reconnecting...")
                if not self.connect():
                    return False
            
            self.logger.info("Selecting INBOX...")
            status, data = self.mail.select('inbox')
            if status != 'OK':
                self.logger.error("Failed to select inbox")
                return False
            
            # Ищем ТОЛЬКО НЕПРОЧИТАННЫЕ письма
            status, messages = self.mail.search(None, 'UNSEEN')
            if status != 'OK':
                self.logger.error("Failed to search unseen emails")
                return False
            
            email_ids = messages[0].split()
            self.logger.info(f"Found {len(email_ids)} unseen emails")
            
            processed_count = 0
            for mail_id in email_ids:
                try:
                    mail_id_str = mail_id.decode()
                    self.logger.info(f"Processing email ID: {mail_id_str}")
                    status, data = self.mail.fetch(mail_id, '(RFC822)')
                    
                    if status != 'OK':
                        self.logger.error(f"Failed to fetch email {mail_id_str}")
                        continue
                    
                    # data[0][1] - содержимое письма в байтах
                    msg = email.message_from_bytes(data[0][1])
                    subject = self.decode_header(msg.get('Subject', ''))
                    
                    # Проверяем наличие ключевой фразы
                    if not contains_key_phrase(subject):
                        self.logger.info(f"Skipping email (no key phrase): {subject}")
                        # Помечаем как прочитанное, чтобы не обрабатывать снова
                        self.mail.store(mail_id, '+FLAGS', '\\Seen')
                        continue
                    
                    # Обработка письма
                    if self.process_message(msg):
                        # Помечаем письмо как прочитанное после успешной обработки
                        self.mail.store(mail_id, '+FLAGS', '\\Seen')
                        processed_count += 1
                    else:
                        # Если не удалось обработать, оставляем непрочитанным? Или пометим?
                        # Пометим прочитанным, чтобы не зацикливаться
                        self.mail.store(mail_id, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    self.logger.error(f"Error processing email {mail_id_str}: {str(e)}")
            
            self.logger.info(f"Processed {processed_count} emails with responses")
            return True
        except Exception as e:
            self.logger.error(f"Fetch error: {str(e)}")
            return False
        finally:
            if self.mail:
                try:
                    self.mail.close()
                except:
                    pass
                self.mail.logout()
    
    def process_message(self, msg):
        try:
            subject = self.decode_header(msg.get('Subject', ''))
            self.logger.info(f"Processing email with subject: {subject}")
            
            # Шаблон для извлечения данных: (user_id-email_part)
            pattern = r'\((\d+)-([\w\.-]+)\)'
            match = re.search(pattern, subject)
            
            if not match:
                self.logger.warning("Could not extract user ID and email part from subject")
                return False
            
            user_id = int(match.group(1))
            original_mail = match.group(2).strip()
            
            # Извлекаем название продукта: ищем после ключевой фразы до скобки
            # Находим начало фразы "Request for Delivery of" (без учета регистра)
            start_idx = subject.lower().find("request for delivery of")
            if start_idx == -1:
                self.logger.warning("Key phrase found but not in expected position")
                return False
            
            product_start = start_idx + len("Request for Delivery of")
            product_end = subject.find("(", product_start)
            
            if product_end == -1:
                self.logger.warning("Could not find product name in subject")
                return False
            
            product = subject[product_start:product_end].strip()
            product = clean_product_name(product)
            
            # Получаем email отправителя
            from_email = self.get_email_from_header(msg.get('From', ''))
            
            # Обработка даты
            date_str = msg.get('Date')
            try:
                if date_str:
                    # Преобразуем строку даты в aware datetime объект
                    email_date = parsedate_to_datetime(date_str)
                    # Если дата наивная, конвертируем в текущий часовой пояс
                    if timezone.is_naive(email_date):
                        email_date = timezone.make_aware(email_date)
                else:
                    raise ValueError("No date in email header")
            except Exception as e:
                self.logger.warning(f"Date parsing error: {str(e)}")
                email_date = timezone.now()
            # date_str = msg.get('Date')
            # email_date = None
            # if date_str:
            #     date_tuple = parsedate_tz(date_str)
            #     if date_tuple:
            #         email_date = datetime.fromtimestamp(mktime_tz(date_tuple))
            # if not email_date:
            #     email_date = datetime.now()
            #     self.logger.warning("Using current date for email date")
            
            # Получаем тело письма
            body = self.get_email_body(msg)
            
            # Получаем вложения
            attachments = self.get_attachments(msg)
            
            # Получаем Message-ID
            message_id = msg.get('Message-ID', '')
            
            # Проверяем дубликаты
            if message_id and SupplierResponse.objects.filter(message_id=message_id).exists():
                self.logger.info(f"Duplicate email by message_id: {message_id}")
                return False
            
            if SupplierResponse.objects.filter(
                email=from_email, 
                date=email_date, 
                product=product
            ).exists():
                self.logger.info(f"Duplicate email by email+date+product: {from_email}, {email_date}, {product}")
                return False
            
            # Сохраняем в базу
            try:
                user = User.objects.get(id=user_id)
                response = SupplierResponse.objects.create(
                    user=user,
                    product=product,
                    email=from_email,
                    original_mail=original_mail,
                    subject=subject,
                    message=body,
                    date=email_date,
                    message_id=message_id
                )
                
                # Сохраняем первое вложение
                if attachments:
                    filename, content = attachments[0]
                    response.attachment.save(filename, ContentFile(content))
                    self.logger.info(f"Saved attachment: {filename}")
                
                self.logger.info(f"Saved response to database: ID {response.id}")
                return True
                
            except User.DoesNotExist:
                self.logger.error(f"User with ID {user_id} does not exist")
            except Exception as e:
                self.logger.error(f"Database save error: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")
        
        return False
    
    def decode_header(self, header):
        if not header:
            return ""
        try:
            decoded = decode_header(header)
            result = ""
            for part, encoding in decoded:
                if isinstance(part, bytes):
                    try:
                        result += part.decode(encoding or 'utf-8', 'replace')
                    except:
                        result += part.decode('utf-8', 'replace')
                else:
                    result += part
            return result.replace('\n', ' ').replace('\r', ' ').strip()
        except Exception as e:
            self.logger.error(f"Header decoding error: {str(e)}")
            return str(header)
    
    def get_email_from_header(self, header):
        """Извлекает email из заголовка From."""
        if not header:
            return ""
        # Пример: "John Doe <john@example.com>"
        if '<' in header and '>' in header:
            start = header.find('<') + 1
            end = header.find('>', start)
            if end != -1:
                return header[start:end]
        # Если в заголовке просто email
        return header
    
    def get_email_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Пропускаем вложения
                if "attachment" in content_disposition:
                    continue
                    
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body += part.get_payload(decode=True).decode(charset, 'replace')
                    except Exception as e:
                        self.logger.warning(f"Text decoding error: {str(e)}")
                        body += str(part.get_payload(decode=True))
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, 'replace')
            except Exception as e:
                self.logger.warning(f"Text decoding error: {str(e)}")
                body = str(msg.get_payload(decode=True))
        
        return body
    
    def get_attachments(self, msg):
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
                    content = part.get_payload(decode=True)
                    
                    # Проверка размера файла
                    max_size = getattr(settings, 'MAX_ATTACHMENT_SIZE', 25 * 1024 * 1024)
                    if len(content) > max_size:
                        self.logger.warning(f"Attachment too big: {filename} ({len(content)} bytes)")
                        continue
                        
                    attachments.append((filename, content))
        return attachments