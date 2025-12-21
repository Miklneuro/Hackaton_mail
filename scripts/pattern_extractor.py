import os
import re
import email
import html
from pathlib import Path

def clean_text(text: str) -> str:
    """Очищает текст от технического мусора."""
    if not text:
        return ""
    # Декодируем HTML-сущности
    text = html.unescape(text)
    # Удаляем HTML-теги
    text = re.sub(r'<[^>]+>', ' ', text)
    # Удаляем ссылки и email
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'\S+@\S+\.\S+', ' ', text)
    # Удаляем HTML-сущности вроде &nbsp;
    text = re.sub(r'&[a-z]+;', ' ', text)
    # Удаляем hex-последовательности (часто в заголовках .eml)
    text = re.sub(r'\b[0-9a-f]{8,}\b', ' ', text, flags=re.IGNORECASE)
    # Оставляем только буквы, цифры, пробелы, кириллицу
    text = re.sub(r'[^\w\sа-яёА-ЯЁ]', ' ', text)
    # Удаляем короткие слова и одиночные символы
    text = re.sub(r'\b\w{1,2}\b', ' ', text)
    # Нормализуем пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def extract_from_eml(file_path: Path):
    """Извлекает категорию (=имя файла), тему и чистый текст из .eml файла."""
    category = file_path.stem  # имя без расширения
    
    # Читаем как бинарный — это надёжнее для разных кодировок
    try:
        with open(file_path, 'rb') as f:
            msg = email.message_from_binary_file(f)
    except Exception as e:
        return category, f"[Ошибка парсинга EML: {e}]", ""
    
    # Извлекаем тему с поддержкой кодировок (email.header уже обрабатывает =?UTF-8?B?= и т.п.)
    subject = msg.get('subject', '')
    if subject:
        try:
            subject = email.header.decode_header(subject)[0][0]
            if isinstance(subject, bytes):
                # Пробуем разные кодировки
                for enc in ['utf-8', 'cp1251', 'koi8-r', 'iso-8859-1']:
                    try:
                        subject = subject.decode(enc)
                        break
                    except:
                        continue
                else:
                    subject = str(subject)
        except:
            subject = str(subject)
    else:
        subject = "Без темы"
    
    # Извлекаем текст
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    # Пытаемся декодировать с разными кодировками
                    if isinstance(payload, bytes):
                        for enc in ['utf-8', 'cp1251', 'koi8-r', 'iso-8859-1']:
                            try:
                                body += payload.decode(enc)
                                break
                            except:
                                continue
                        else:
                            body += payload.decode('utf-8', errors='replace')
                    else:
                        body += str(payload)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            if isinstance(payload, bytes):
                for enc in ['utf-8', 'cp1251', 'koi8-r', 'iso-8859-1']:
                    try:
                        body = payload.decode(enc)
                        break
                    except:
                        continue
                else:
                    body = payload.decode('utf-8', errors='replace')
            else:
                body = str(payload)
    
    clean_body = clean_text(body)
    return category, subject.strip(), clean_body

def main():
    INPUT_FOLDER = r"D:\Hackaton_mail\data_input"
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "pattern_analysis_report_new.txt")
    
    input_path = Path(INPUT_FOLDER)
    if not input_path.exists():
        print(f"❌ Папка не найдена: {INPUT_FOLDER}")
        return
    
    eml_files = list(input_path.glob("*.eml"))
    if not eml_files:
        print(f"⚠️ В папке {INPUT_FOLDER} нет файлов .eml")
        return
    
    print(f"✅ Найдено {len(eml_files)} .eml файлов. Обработка...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write("ОБРАБОТКА ПИСЕМ ИЗ .EML\n")
        out.write("=" * 60 + "\n\n")
        
        for file_path in eml_files:
            try:
                category, subject, text = extract_from_eml(file_path)
                out.write(f"Категория (имя файла): {category}\n")
                out.write(f"Тема (Subject): {subject}\n")
                out.write(f"Длина текста: {len(text)} символов\n")
                out.write("Текст:\n")
                out.write(text + "\n")
                out.write("-" * 60 + "\n\n")
            except Exception as e:
                out.write(f"Категория: {file_path.stem}\n")
                out.write(f"Ошибка: не удалось обработать файл — {e}\n")
                out.write("-" * 60 + "\n\n")
    
    print(f"✅ Готово! Отчёт сохранён: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()