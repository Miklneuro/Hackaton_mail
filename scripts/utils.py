import os
from pathlib import Path
import shutil
import json
import re
from email.header import decode_header

def decode_subject(subject: str) -> str:
    """Декодирует тему письма из формата =?UTF-8?B?...= в читаемый текст."""
    if not subject:
        return ""
    
    try:
        decoded_parts = decode_header(subject)
        decoded_subject = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_subject += part.decode(encoding, errors='ignore')
                else:
                    # Пробуем разные кодировки
                    for enc in ['utf-8', 'cp1251', 'koi8-r', 'iso-8859-5']:
                        try:
                            decoded_subject += part.decode(enc, errors='strict')
                            break
                        except:
                            continue
                    else:
                        decoded_subject += part.decode('utf-8', errors='ignore')
            else:
                decoded_subject += str(part)
        return decoded_subject.strip()
    except Exception as e:
        print(f"⚠️ Ошибка декодирования темы '{subject[:30]}...': {e}")
        return subject

def extract_true_category_from_filename(filename: str) -> str:
    """Извлекает истинную категорию из имени файла."""
    if not filename:
        raise ValueError("Имя файла не может быть пустым")
    
    # Удаляем расширение файла
    filename_without_ext = Path(filename).stem
    filename_lower = filename_without_ext.lower()
    
    # ЖЕСТКИЙ СЛОВАРЬ СОПОСТАВЛЕНИЯ АНГЛИЙСКИХ ИМЕН С РУССКИМИ КАТЕГОРИЯМИ
    # Ключи - английские названия из датасета, значения - русские категории из new_cats.txt
    category_mapping = {
        # Основные категории из датасета
        'business_and_correspondence': 'Бизнес-корреспонденция',
        'financial_transactions_and_cheques': 'Финансовые операции',
        'harm_content': 'Неприемлемый контент',
        'transport_and_travel': 'Транспорт и путешествия',
        'newsletters': 'Новостные рассылки',
        'registration_confirmation': 'Регистрация и подтверждение',
        'promotional_mailing': 'Рекламная рассылка',
        'system_and_service_notifications': 'Системные уведомления',
        'technical_support': 'Техническая поддержка',
        'vacancies_careers': 'Вакансии и карьера',
        'vacancies_and_career': 'Вакансии и карьера',
        
        # Категория "Другое" ТОЛЬКО для файлов с 'other'
        'other': 'Другое',
    }
    
    # Проверяем каждое сопоставление в словаре
    for eng_name, rus_category in category_mapping.items():
        if eng_name in filename_lower:
            return rus_category
    
    # Если не нашли соответствие - вызываем исключение
    raise ValueError(f"Не удалось определить категорию для файла: {filename}")

def load_categories(file_path: str) -> dict:
    """Загружает категории из файла. Комбинирует название и описание для лучшего контекста."""
    categories = {}
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            if ":" in line:
                name, description = line.split(":", 1)
                name = name.strip()
                description = description.strip()
                
                # Комбинируем название и описание с ключевыми словами на обоих языках
                # Добавляем английские эквиваленты для основных категорий
                enhanced_description = f"{name}. {description}"
                
                # Добавляем английские ключевые слова для мультиязычности
                english_keywords = {
                    "Техническая поддержка": "technical support, help desk, IT support, troubleshooting",
                    "Финансовые операции": "financial transactions, payments, invoices, bills, accounting",
                    "Вакансии и карьера": "vacancies, careers, jobs, recruitment, CV, resume",
                    "Рекламная рассылка": "advertising, marketing, promotion, commercial offers",
                    "Новостные рассылки": "newsletters, news, updates, announcements",
                    "Регистрация и подтверждение": "registration, confirmation, account, verification",
                    "Транспорт и путешествия": "transport, travel, tickets, booking, flights, hotels",
                    "Неприемлемый контент": "spam, inappropriate content, adult, violence",
                    "Бизнес-корреспонденция": "business correspondence, partners, contracts, negotiations",
                    "Системные уведомления": "system notifications, alerts, reports, automated messages",
                    "Другое": "other, miscellaneous, uncategorized"
                }
                
                if name in english_keywords:
                    enhanced_description += f". {english_keywords[name]}"
                
                categories[name] = enhanced_description
                print(f"   📍 {name}: {enhanced_description[:80]}...")
            else:
                categories[line] = line
    
    print(f"\n📂 Загружено категорий: {len(categories)}")
    return categories

def clear_output_folder(output_folder: str):
    """Очищает папку data_output."""
    output_path = Path(output_folder)
    if output_path.exists():
        for file in output_path.iterdir():
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)
    else:
        output_path.mkdir(parents=True, exist_ok=True)

def save_results_json(results: list, output_file: str):
    """Сохраняет результаты в JSON файл."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

def save_results_csv(results: list, output_file: str):
    """Сохраняет результаты в CSV файл."""
    import pandas as pd
    
    flat_data = []
    for result in results:
        row = {
            'filename': result.get('filename', ''),
            'subject': result.get('subject_decoded', result.get('subject', '')),
            'text_preview': result.get('body_preview', ''),
            'top_category': '',
            'top_score': 0.0,
            'processed': result.get('processed', False)
        }
        
        if result.get('categories'):
            row['top_category'] = result['categories'][0][0]
            row['top_score'] = result['categories'][0][1]
            
            for i, (cat, score) in enumerate(result['categories'][:5]):
                row[f'category_{i+1}'] = cat
                row[f'score_{i+1}'] = f"{score:.3f}"
        
        flat_data.append(row)
    
    df = pd.DataFrame(flat_data)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')