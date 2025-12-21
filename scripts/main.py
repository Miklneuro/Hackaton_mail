import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from parser import parse_emails
from classifier import classify_emails
from utils import clear_output_folder, decode_subject
from exporter import export_results, generate_stats, print_stats
from metrics import calculate_metrics, save_metrics_to_file  # Импортируем новый модуль

def main():
    base_dir = os.path.dirname(current_dir)
    
    input_folder = os.path.join(base_dir, "data_input")
    output_folder = os.path.join(base_dir, "data_output")
    categories_file = os.path.join(base_dir, "categories", "new_cats.txt")
    
    print("=" * 70)
    print("🤖 MAIL LENS - Интеллектуальный классификатор писем")
    print("=" * 70)
    print(f"📁 Входная папка: {input_folder}")
    print(f"📁 Выходная папка: {output_folder}")
    print(f"📄 Файл категорий: {categories_file}")
    print("-" * 70)
    
    # Проверка существования путей
    if not os.path.exists(input_folder):
        print(f"❌ Папка {input_folder} не существует!")
        return
    
    files = [f for f in os.listdir(input_folder) if f.endswith(('.eml', '.msg'))]
    if not files:
        print(f"❌ В папке нет .eml или .msg файлов!")
        return
    
    print(f"📧 Найдено файлов: {len(files)}")
    
    # Очистка выходной папки (опционально, можно закомментировать)
    clear_output_folder(output_folder)
    
    # Парсинг писем
    print("\n🔍 Парсинг писем...")
    try:
        emails = parse_emails(input_folder)
        print(f"✅ Распарсено писем: {len(emails)}")
    except Exception as e:
        print(f"❌ Ошибка при парсинге писем: {e}")
        return
    
    # Классификация писем
    print("\n🤖 Классификация писем...")
    try:
        results = classify_emails(emails, categories_file, top_n=5, threshold=0.25)
        print(f"✅ Классифицировано писем: {len(results)}")
    except Exception as e:
        print(f"❌ Ошибка при классификации: {e}")
        return
    
    # Добавляем декодированные темы в результаты (для удобства)
    for result in results:
        result['subject_decoded'] = decode_subject(result.get('subject', ''))
    
    # === ВЫЗОВ ЭКСПОРТЕРА ===
    print("\n" + "=" * 70)
    print("💾 ЭКСПОРТ РЕЗУЛЬТАТОВ")
    print("=" * 70)
    
    # Экспорт в JSON и CSV
    try:
        exported_files = export_results(
            results=results,
            output_dir=output_folder,
            formats=['json', 'csv'],
            filename_prefix='mail_lens_results'
        )
        
        print(f"\n✅ Экспорт завершен!")
        for fmt, filepath in exported_files.items():
            print(f"   📄 {fmt.upper()}: {filepath}")
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")
    
    # Генерация и вывод статистики
    print("\n" + "=" * 70)
    stats = generate_stats(results)
    print_stats(stats)
    
    # РАСЧЕТ МЕТРИК
    print("\n" + "=" * 70)
    print("📊 РАСЧЕТ МЕТРИК КЛАССИФИКАЦИИ")
    print("=" * 70)
    
    try:
        # Рассчитываем метрики
        metrics_data = calculate_metrics(results)
        
        # Сохраняем метрики в файл
        if metrics_data:
            metrics_file = save_metrics_to_file(
                metrics_data=metrics_data,
                output_dir=output_folder,
                filename_prefix='classification_metrics'
            )
            
            if metrics_file:
                print(f"\n✅ Метрики успешно рассчитаны и сохранены")
    except Exception as e:
        print(f"⚠️ Ошибка при расчете метрик: {e}")
    
    # Краткий вывод результатов
    print("\n" + "=" * 70)
    print("📋 КРАТКИЕ РЕЗУЛЬТАТЫ:")
    print("=" * 70)
    
    for i, result in enumerate(results[:5], 1):  # Показываем первые 5 результатов
        if result.get('processed', False):
            categories = result.get('categories', [])
            if categories:
                print(f"\n{i}. 📨 {result['filename']}")
                print(f"   📝 Тема: {result['subject_decoded'][:80]}...")
                print(f"   🏷️  Топ категория: {categories[0][0]} ({categories[0][1]:.3f})")
    
    if len(results) > 5:
        print(f"\n... и еще {len(results) - 5} писем")
    
    print("\n" + "=" * 70)
    print(f"🎯 Готово! Проверьте папку: {output_folder}")
    print("=" * 70)

if __name__ == "__main__":
    main()