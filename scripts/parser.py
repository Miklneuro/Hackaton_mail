import os
import re
from email import message_from_file
from extract_msg import Message as MsgFile
import chardet  # Для автоопределения кодировки

def parse_emails(folder_path: str) -> list:
    """
    Парсит все .eml и .msg файлы из указанной папки.
    :param folder_path: Путь к папке с входящими письмами.
    :return: Список словарей с данными писем.
    """
    emails = []
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if file_name.endswith(".eml"):
            email_data = parse_eml(file_path)
        elif file_name.endswith(".msg"):
            email_data = parse_msg(file_path)
        else:
            continue  # Пропускаем неподдерживаемые форматы
        
        if email_data:  # Добавляем только если парсинг успешен
            emails.append(email_data)
    
    print(f"✅ Успешно распарсено писем: {len(emails)}")
    return emails

def parse_eml(file_path: str) -> dict:
    """Парсит .eml файл."""
    try:
        # Определяем кодировку файла
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'
        
        # Пробуем разные кодировки если обнаружена неправильная
        for enc in [encoding, 'utf-8', 'cp1251', 'windows-1251', 'koi8-r', 'iso-8859-5', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    msg = message_from_file(f)
                break
            except UnicodeDecodeError:
                continue
        else:
            # Если все кодировки не подошли, пробуем с игнорированием ошибок
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                msg = message_from_file(f)
        
        return {
            "filename": os.path.basename(file_path),
            "subject": msg.get("Subject", ""),
            "body": get_email_body(msg),
            "attachments": []  # (Добавьте обработку вложений при необходимости)
        }
    except Exception as e:
        print(f"❌ Ошибка парсинга файла {os.path.basename(file_path)}: {e}")
        return None

def parse_msg(file_path: str) -> dict:
    """Парсит .msg файл."""
    try:
        msg = MsgFile(file_path)
        return {
            "filename": os.path.basename(file_path),
            "subject": msg.subject,
            "body": msg.body,
            "attachments": [att.longFilename for att in msg.attachments]
        }
    except Exception as e:
        print(f"❌ Ошибка парсинга .msg файла {os.path.basename(file_path)}: {e}")
        return None

def html_to_text(html_content: bytes) -> str:
    """Конвертирует HTML в текст без использования BeautifulSoup."""
    try:
        # Пробуем разные кодировки
        for encoding in ['utf-8', 'cp1251', 'windows-1251', 'koi8-r', 'iso-8859-5', 'latin-1']:
            try:
                html_decoded = html_content.decode(encoding, errors='strict')
                break
            except UnicodeDecodeError:
                continue
        else:
            html_decoded = html_content.decode('utf-8', errors='ignore')
        
        # Простая очистка HTML тегов с использованием регулярных выражений
        # Удаляем скрипты и стили
        html_decoded = re.sub(r'<(script|style).*?>.*?</\1>', '', html_decoded, flags=re.DOTALL | re.IGNORECASE)
        
        # Заменяем HTML-сущности
        html_decoded = html_decoded.replace('&nbsp;', ' ')
        html_decoded = html_decoded.replace('&amp;', '&')
        html_decoded = html_decoded.replace('&lt;', '<')
        html_decoded = html_decoded.replace('&gt;', '>')
        html_decoded = html_decoded.replace('&quot;', '"')
        
        # Удаляем все остальные HTML теги
        html_decoded = re.sub(r'<[^>]+>', ' ', html_decoded)
        
        # Удаляем лишние пробелы и переносы строк
        html_decoded = re.sub(r'\s+', ' ', html_decoded)
        html_decoded = html_decoded.strip()
        
        return html_decoded
    except Exception as e:
        print(f"⚠️  Ошибка при конвертации HTML: {e}")
        # Пытаемся просто декодировать как текст
        try:
            return html_content.decode('utf-8', errors='ignore')[:1000]
        except:
            return ""

def get_email_body(msg) -> str:
    """Извлекает тело письма из объекта email."""
    body = ""
    
    # Сначала пытаемся извлечь тему письма, так как она содержит важную информацию
    subject = msg.get("Subject", "")
    try:
        # Пытаемся декодировать тему из формата =?UTF-8?B?...=
        from email.header import decode_header
        decoded_parts = decode_header(subject)
        decoded_subject = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_subject += part.decode(encoding, errors='ignore')
                else:
                    decoded_subject += part.decode('utf-8', errors='ignore')
            else:
                decoded_subject += part
        if decoded_subject.strip():
            body += f"Тема письма: {decoded_subject}\n\n"
    except Exception as e:
        # Если декодирование не удалось, оставляем как есть
        if subject.strip():
            body += f"Тема письма: {subject}\n\n"
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # Текстовое тело
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    # Пробуем разные кодировки
                    for encoding in ['utf-8', 'cp1251', 'windows-1251', 'koi8-r', 'iso-8859-5', 'latin-1']:
                        try:
                            body += payload.decode(encoding, errors='strict')
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Если ни одна кодировка не подошла, используем игнорирование ошибок
                        body += payload.decode('utf-8', errors='ignore')
            
            # HTML тело
            elif content_type == "text/html" and "attachment" not in content_disposition:
                try:
                    html_content = part.get_payload(decode=True)
                    if html_content:
                        html_text = html_to_text(html_content)
                        if html_text:
                            body += html_text + "\n"
                except Exception as e:
                    print(f"⚠️  Ошибка при обработке HTML части: {e}")
    else:
        # Не multipart письмо - пытаемся получить содержимое напрямую
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                content_type = msg.get_content_type()
                
                if content_type == 'text/plain':
                    # Пробуем разные кодировки
                    for encoding in ['utf-8', 'cp1251', 'windows-1251', 'koi8-r', 'iso-8859-5', 'latin-1']:
                        try:
                            body += payload.decode(encoding, errors='strict')
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        body += payload.decode('utf-8', errors='ignore')
                
                elif content_type == 'text/html':
                    html_text = html_to_text(payload)
                    if html_text:
                        body += html_text
                
                else:
                    # Для других типов пытаемся декодировать как текст
                    try:
                        body += payload.decode('utf-8', errors='ignore')
                    except:
                        pass
        except Exception as e:
            print(f"⚠️  Ошибка при обработке не-multipart письма: {e}")
    
    return body.strip()