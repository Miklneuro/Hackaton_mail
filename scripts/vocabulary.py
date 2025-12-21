import re
from collections import defaultdict, Counter
from pathlib import Path

def clean_word(word: str) -> str:
    """Удаляет знаки препинания с краёв слова и приводит к нижнему регистру."""
    return re.sub(r'^\W+|\W+$', '', word).lower()

def build_category_dictionaries(report_file: str, output_file: str):
    # 1. Парсим файл
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Разделяем на блоки по разделителю
    blocks = content.split("-" * 60)
    
    # Словарь: категория -> список слов
    category_words = defaultdict(list)
    # Словарь: категория -> оригинальное имя (для красивого вывода)
    category_names = {}

    for block in blocks:
        if "Категория (имя файла):" not in block:
            continue

        # Извлекаем категорию (имя файла)
        cat_line = [line for line in block.splitlines() if line.startswith("Категория (имя файла):")]
        if not cat_line:
            continue
        filename = cat_line[0].replace("Категория (имя файла):", "").strip()
        
        # Определяем логическую категорию по префиксу (до первого '_')
        if '_' in filename:
            base_cat = filename.split('_')[0]
        else:
            base_cat = filename

        # Приводим к читаемому виду (заменяем подчёркивания на пробелы)
        readable_cat = base_cat.replace('_', ' ').capitalize()
        category_names[base_cat] = readable_cat

        # Извлекаем текст
        text_start = block.find("Текст:") 
        if text_start == -1:
            continue
        text = block[text_start + len("Текст:"):].strip()

        # Разбиваем на слова "механически"
        raw_words = text.split()
        clean_words = [clean_word(w) for w in raw_words]
        clean_words = [w for w in clean_words if w and len(w) >= 3]  # фильтр коротких

        category_words[base_cat].extend(clean_words)  # ← исправлено: было clean_works

    # 2. Считаем частоту слов по категориям
    category_counters = {cat: Counter(words) for cat, words in category_words.items()}

    # 3. Считаем, в скольких категориях встречается каждое слово
    word_categories = defaultdict(set)
    for cat, counter in category_counters.items():
        for word in counter:
            word_categories[word].add(cat)

    # 4. Для каждой категории строим рейтинг слов: 
    #    приоритет — уникальность (встречается только в этой категории),
    #    затем — частота
    final_dictionaries = {}
    for cat, counter in category_counters.items():
        scored_words = []
        for word, freq in counter.items():
            num_cats = len(word_categories[word])
            # Уникальность: 1 если только в этой категории, иначе 0
            is_unique = 1 if num_cats == 1 else 0
            scored_words.append((word, freq, is_unique))
        
        # Сортировка: сначала уникальные (is_unique=1), потом по частоте убывания
        scored_words.sort(key=lambda x: (-x[2], -x[1]))
        final_dictionaries[cat] = [word for word, _, _ in scored_words]

    # 5. Сохраняем результат
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("СЛОВАРИ ДЛЯ КАТЕГОРИЙ (уникальность + частотность)\n")
        out.write("=" * 60 + "\n\n")
        
        # Сортируем категории в порядке их появления в данных
        ordered_cats = list(category_names.keys())
        for cat_key in ordered_cats:
            readable = category_names[cat_key]
            words = final_dictionaries.get(cat_key, [])
            out.write(f"{readable}:\n")
            out.write(", ".join(words[:50]))  # первые 50 самых релевантных
            out.write("\n\n")

    print(f"✅ Словари сохранены в: {output_file}")

# === ЗАПУСК ===
if __name__ == "__main__":
    # Укажите путь к вашему файлу с обработанными письмами
    INPUT_REPORT = "pattern_analysis_report_new.txt"  # ← замените, если имя другое
    OUTPUT_DICT = "category_dictionaries.txt"
    
    build_category_dictionaries(INPUT_REPORT, OUTPUT_DICT)