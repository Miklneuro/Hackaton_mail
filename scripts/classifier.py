from sentence_transformers import SentenceTransformer, util
from utils import load_categories, decode_subject
import torch
import numpy as np
import os

# === КОНФИГУРАЦИЯ ===
OTHER_CATEGORY_NAME = "Другое"  # Исключительная категория
OTHER_CATEGORY_THRESHOLD = 0.4  #  порог
MIN_CONFIDENCE_FOR_DISPLAY = 0.3  # Минимальная уверенность для нормального отображения

# === ПУТИ ===
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_CACHE_DIR = os.path.join(PROJECT_ROOT, 'model_cache')
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

print(f"🤖 Кэш моделей: {MODEL_CACHE_DIR}")

# === ЗАГРУЗКА МОДЕЛИ ===
print("🤖 Загрузка модели Sentence Transformer...")

try:
    model_name = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
    model = SentenceTransformer(
        model_name,
        cache_folder=MODEL_CACHE_DIR,
        device='cpu'
    )
    print(f"✅ Модель '{model_name}' загружена в {MODEL_CACHE_DIR}")

except Exception as e:
    print(f"⚠️ Ошибка загрузки основной модели: {e}")
    try:
        print("🔄 Пробуем упрощенную модель: paraphrase-multilingual-MiniLM-L12-v2")
        model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2',
            cache_folder=MODEL_CACHE_DIR,
            device='cpu'
        )
        model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
        print("✅ Упрощенная модель загружена")
    except Exception as e2:
        print(f"⚠️ Ошибка загрузки упрощенной модели: {e2}")
        try:
            print("🔄 Пробуем легкую модель: all-MiniLM-L6-v2")
            model = SentenceTransformer(
                'all-MiniLM-L6-v2',
                cache_folder=MODEL_CACHE_DIR,
                device='cpu'
            )
            model_name = 'all-MiniLM-L6-v2'
            print("✅ Легкая модель загружена")
        except Exception as e3:
            print(f"❌ Критическая ошибка: не удалось загрузить ни одну модель")
            raise

# === ИНФОРМАЦИЯ О ЗАГРУЖЕННОЙ МОДЕЛИ ===
print(f"\n📊 Информация о модели:")
print(f"   • Имя: {model_name}")
print(f"   • Размерность эмбеддингов: {model.get_sentence_embedding_dimension()}")
print(f"   • Макс. длина последовательности: {model.max_seq_length}")
print(f"   • Поддерживаемые языки: мультиязычная (включая RU/EN)")
print(f"\n⚙️  Логика категории '{OTHER_CATEGORY_NAME}':")
print(f"   • Порог для '{OTHER_CATEGORY_NAME}': {OTHER_CATEGORY_THRESHOLD}")
print(f"   • Если лучшая категория < {OTHER_CATEGORY_THRESHOLD} → '{OTHER_CATEGORY_NAME}'")


def preprocess_text(text: str, subject: str = "") -> str:
    """Очищает и предобрабатывает текст письма с учётом темы."""
    if not text and not subject:
        return ""

    try:
        decoded_subject = decode_subject(subject)
    except Exception as e:
        print(f"⚠️  Ошибка декодирования темы: {e}")
        decoded_subject = subject[:100] if subject else ""

    # Комбинируем тему и тело письма
    enhanced_text = f"{decoded_subject}. {decoded_subject}. {decoded_subject}. {text}"

    # Удаляем лишние пробелы и переносы
    enhanced_text = ' '.join(enhanced_text.split())

    # Ограничиваем длину, но сохраняем важные части
    max_length = 4000
    if len(enhanced_text) > max_length:
        subject_part = f"{decoded_subject}. {decoded_subject}. {decoded_subject}."
        body_part = text[:max_length - len(subject_part) - 100]
        enhanced_text = subject_part + " " + body_part + "..."

    return enhanced_text


def safe_encode_text(text: str, max_retries: int = 2) -> torch.Tensor:
    """Безопасное кодирование текста с обработкой ошибок."""
    for attempt in range(max_retries):
        try:
            return model.encode(text, convert_to_tensor=True, show_progress_bar=False)
        except Exception as e:
            print(f"⚠️  Ошибка кодирования текста (попытка {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
            # Пробуем обрезать текст на случай слишком длинных текстов
            text = text[:3000] + " [ТЕКСТ ОБРЕЗАН]"


def classify_emails(emails: list, categories_file: str, top_n: int = 5, threshold: float = 0.1) -> list:
    """
    Классифицирует список писем по категориям.
    :param threshold: Порог для фильтрации низких сходств
    """
    try:
        categories = load_categories(categories_file)
        print(f"📂 Загружено категорий: {len(categories)}")

        if not categories:
            print("❌ Файл категорий пуст!")
            return []

    except Exception as e:
        print(f"❌ Ошибка загрузки категорий: {e}")
        return []

    results = []

    # Подготавливаем эмбеддинги категорий один раз
    print("🔧 Подготовка эмбеддингов категорий...")
    try:
        category_names = list(categories.keys())
        category_descriptions = list(categories.values())
        category_embeddings = model.encode(category_descriptions, convert_to_tensor=True)
        print(f"✅ Эмбеддинги категорий подготовлены: {len(category_names)}")
    except Exception as e:
        print(f"❌ Ошибка подготовки эмбеддингов категорий: {e}")
        return results

    # Статистика
    stats = {
        'total': 0,
        'successful': 0,
        'to_other': 0,
        'errors': 0,
        'confidences': []
    }

    for i, email in enumerate(emails, 1):
        email_result = {
            "filename": email.get("filename", f"email_{i}"),
            "subject": email.get("subject", ""),
            "processed": False,
            "categories": [],
            "error": None
        }
        
        try:
            filename = email.get("filename", f"email_{i}")
            print(f"\n📨 Обработка {i}/{len(emails)}: {filename}")

            subject = email.get("subject", "")
            body = email.get("body", "")

            # Проверяем наличие текста
            if not body and not subject:
                print(f"⚠️  Письмо пустое, пропускаем")
                email_result.update({
                    "subject_decoded": "",
                    "body_preview": "",
                    "categories": [("Пустое письмо", 0.0)],
                    "error": "Пустое письмо"
                })
                results.append(email_result)
                continue

            # Усиливаем текст с помощью темы
            try:
                processed_text = preprocess_text(body, subject)
                decoded_subject = decode_subject(subject) if subject else ""
            except Exception as e:
                print(f"⚠️  Ошибка предобработки текста: {e}")
                # Пробуем использовать сырой текст
                processed_text = body[:2000] if body else subject
                decoded_subject = subject[:100] if subject else ""

            print(f"📝 Текст: {len(processed_text)} символов")
            if decoded_subject:
                print(f"📄 Тема (декодирована): {decoded_subject[:100]}...")

            if not processed_text.strip():
                print(f"⚠️  Письмо пустое после предобработки")
                email_result.update({
                    "subject_decoded": decoded_subject,
                    "body_preview": "",
                    "categories": [("Пустое письмо", 0.0)],
                    "error": "Пустое письмо после предобработки"
                })
                results.append(email_result)
                continue

            # Классификация
            try:
                category_scores = classify_text(
                    processed_text,
                    categories,
                    category_embeddings,
                    top_n,
                    threshold
                )
                
                stats['total'] += 1
                stats['successful'] += 1

                if category_scores:
                    best_category, best_confidence = category_scores[0]
                    stats['confidences'].append(best_confidence)
                    
                    # Применяем логику с категорией "Другое"
                    if best_confidence < OTHER_CATEGORY_THRESHOLD:
                        # Письмо идет в категорию "Другое"
                        final_category_scores = [(OTHER_CATEGORY_NAME, best_confidence)]
                        stats['to_other'] += 1
                        
                        if best_confidence < MIN_CONFIDENCE_FOR_DISPLAY:
                            quality_note = " (ОЧЕНЬ НИЗКАЯ УВЕРЕННОСТЬ)"
                        else:
                            quality_note = ""
                        
                        print(f"🏷️  Категория: {OTHER_CATEGORY_NAME} ({best_confidence:.3f}){quality_note}")
                        if best_confidence > 0.1:  # Показываем только если была какая-то уверенность
                            print(f"   ⚠️  Исходная лучшая категория: '{best_category}' с уверенностью {best_confidence:.3f}")
                    else:
                        # Оставляем оригинальные категории
                        final_category_scores = category_scores
                        top_cat, top_score = category_scores[0]
                        print(f"🏷️  Топ категория: {top_cat} ({top_score:.3f})")
                        
                        # Показываем дополнительные категории если они есть
                        if len(category_scores) > 1:
                            for j, (cat, score) in enumerate(category_scores[1:3], 2):
                                if score > threshold:
                                    print(f"   {j}. {cat} ({score:.3f})")
                else:
                    # Если нет категорий выше порога threshold
                    final_category_scores = [(OTHER_CATEGORY_NAME, 0.0)]
                    stats['to_other'] += 1
                    print(f"🏷️  Категория: {OTHER_CATEGORY_NAME} (0.000)")
                    print(f"   ⚠️  Нет категорий выше порога {threshold}")

                confidence_score = final_category_scores[0][1] if final_category_scores else 0.0

                email_result.update({
                    "subject_decoded": decoded_subject,
                    "body_preview": processed_text[:300],
                    "categories": final_category_scores,
                    "processed": True,
                    "confidence": confidence_score,
                    "is_other_category": (final_category_scores[0][0] == OTHER_CATEGORY_NAME if final_category_scores else False)
                })

            except Exception as e:
                print(f"❌ Ошибка при классификации письма: {e}")
                stats['errors'] += 1
                email_result.update({
                    "subject_decoded": decoded_subject,
                    "body_preview": processed_text[:100] if processed_text else "",
                    "categories": [("Ошибка классификации", 0.0)],
                    "error": f"Ошибка классификации: {str(e)[:100]}"
                })

        except Exception as e:
            print(f"❌ Критическая ошибка при обработке письма: {e}")
            import traceback
            traceback.print_exc()
            stats['errors'] += 1
            email_result["error"] = f"Критическая ошибка: {str(e)[:100]}"

        results.append(email_result)

    # Вывод статистики
    print(f"\n📊 СТАТИСТИКА ОБРАБОТКИ:")
    print(f"   • Всего писем: {len(emails)}")
    print(f"   • Успешно обработано: {stats['successful']}")
    print(f"   • С ошибками: {stats['errors']}")
    
    if stats['successful'] > 0:
        success_rate = (stats['successful'] / len(emails)) * 100
        print(f"   • Успешность: {success_rate:.1f}%")
    
    if stats['confidences']:
        avg_conf = sum(stats['confidences']) / len(stats['confidences'])
        print(f"📊 Средняя уверенность: {avg_conf:.3f}")
        print(f"📊 Минимальная уверенность: {min(stats['confidences']):.3f}")
        print(f"📊 Максимальная уверенность: {max(stats['confidences']):.3f}")
    
    if stats['total'] > 0:
        other_percentage = (stats['to_other'] / stats['total']) * 100
        print(f"📊 Писем в категорию '{OTHER_CATEGORY_NAME}': {stats['to_other']}/{stats['total']} ({other_percentage:.1f}%)")

    return results


def classify_text(text: str, categories: dict, category_embeddings=None, top_n: int = 5,
                  threshold: float = 0.1) -> list:
    """Классифицирует текст по категориям. БЕЗ SOFTMAX."""
    if not text.strip():
        return [("Пустое письмо", 0.0)]

    try:
        # Безопасное кодирование текста
        text_embedding = safe_encode_text(text)

        # Если эмбеддинги категорий не переданы, вычисляем их
        if category_embeddings is None:
            category_descriptions = list(categories.values())
            category_embeddings = model.encode(category_descriptions, convert_to_tensor=True)

        # Вычисляем косинусное сходство
        similarities = util.cos_sim(text_embedding, category_embeddings)[0]
        
        # Нормализуем в [0, 1]
        similarities_np = similarities.cpu().numpy()
        normalized_similarities = (similarities_np + 1) / 2

        # Собираем результаты
        results = []
        category_names = list(categories.keys())

        for i, category_name in enumerate(category_names):
            confidence = float(normalized_similarities[i])
            results.append((category_name, confidence))

        # Сортируем по убыванию уверенности
        results.sort(key=lambda x: x[1], reverse=True)

        # Применяем порог
        normalized_threshold = (threshold + 1) / 2 if threshold < 0 else threshold
        filtered_results = [r for r in results if r[1] >= normalized_threshold]

        # Ограничиваем количество результатов
        return filtered_results[:top_n]

    except Exception as e:
        print(f"❌ Ошибка при классификации текста: {e}")
        # Возвращаем пустой список, вызывающая функция обработает это
        return []