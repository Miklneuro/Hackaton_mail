"""
exporter.py - Модуль для экспорта результатов классификации в различные форматы.
"""

import json
import csv
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def export_to_json(results: List[Dict[str, Any]], output_file: str) -> str:
    """
    Экспортирует результаты в JSON файл.
    
    Args:
        results: Список словарей с результатами классификации
        output_file: Путь к выходному JSON файлу
        
    Returns:
        str: Путь к сохраненному файлу
    """
    try:
        # Добавляем метаданные
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_emails": len(results),
                "successful_emails": len([r for r in results if r.get("processed", False)]),
                "format": "json"
            },
            "results": results
        }
        
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Сохраняем в JSON с поддержкой кириллицы
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON экспортирован: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте в JSON: {e}")
        raise

def export_to_csv(results: List[Dict[str, Any]], output_file: str) -> str:
    """
    Экспортирует результаты в CSV файл.
    
    Args:
        results: Список словарей с результатами классификации
        output_file: Путь к выходному CSV файлу
        
    Returns:
        str: Путь к сохраненному файлу
    """
    try:
        # Преобразуем в плоский формат для CSV
        flat_data = []
        
        for result in results:
            row = {
                'filename': result.get('filename', ''),
                'subject': result.get('subject_decoded', result.get('subject', '')[:200]),
                'body_preview': result.get('body_preview', '')[:300],
                'processed': result.get('processed', False),
                'error': result.get('error', '')
            }
            
            # Добавляем категории
            categories = result.get('categories', [])
            if categories:
                for i, (category, score) in enumerate(categories[:5]):  # Топ-5 категорий
                    row[f'category_{i+1}'] = category
                    row[f'score_{i+1}'] = f"{score:.4f}"
                
                row['top_category'] = categories[0][0]
                row['top_score'] = f"{categories[0][1]:.4f}"
                row['confidence'] = result.get('confidence', 0.0)
            else:
                row['top_category'] = 'Не определено'
                row['top_score'] = 0.0
            
            flat_data.append(row)
        
        # Создаем DataFrame и сохраняем в CSV
        df = pd.DataFrame(flat_data)
        
        # Создаем директорию, если не существует
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Сохраняем с поддержкой кириллицы
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ CSV экспортирован: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте в CSV: {e}")
        raise

def export_to_jsonl(results: List[Dict[str, Any]], output_file: str) -> str:
    """
    Экспортирует результаты в JSONL (JSON Lines) формат.
    Каждая строка - отдельный JSON объект.
    
    Args:
        results: Список словарей с результатами классификации
        output_file: Путь к выходному JSONL файлу
        
    Returns:
        str: Путь к сохраненному файлу
    """
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                # Добавляем timestamp к каждому результату
                result_with_meta = {
                    **result,
                    "export_timestamp": datetime.now().isoformat()
                }
                json_line = json.dumps(result_with_meta, ensure_ascii=False)
                f.write(json_line + '\n')
        
        print(f"✅ JSONL экспортирован: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте в JSONL: {e}")
        raise

def export_results(results: List[Dict[str, Any]], 
                   output_dir: str, 
                   formats: List[str] = ['json', 'csv'],
                   filename_prefix: str = 'mail_lens_results') -> Dict[str, str]:
    """
    Основная функция экспорта в несколько форматов.
    
    Args:
        results: Список словарей с результатами классификации
        output_dir: Директория для сохранения файлов
        formats: Список форматов для экспорта ['json', 'csv', 'jsonl']
        filename_prefix: Префикс для имен файлов
        
    Returns:
        Dict[str, str]: Словарь с путями к сохраненным файлам
    """
    print(f"\n💾 Экспорт результатов в форматы: {', '.join(formats)}")
    
    # Создаем директорию, если не существует
    os.makedirs(output_dir, exist_ok=True)
    
    # Генерируем timestamp для уникальности имен файлов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    exported_files = {}
    
    # Экспорт в запрошенные форматы
    for fmt in formats:
        try:
            if fmt.lower() == 'json':
                output_file = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.json")
                exported_files['json'] = export_to_json(results, output_file)
                
            elif fmt.lower() == 'csv':
                output_file = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.csv")
                exported_files['csv'] = export_to_csv(results, output_file)
                
            elif fmt.lower() == 'jsonl':
                output_file = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.jsonl")
                exported_files['jsonl'] = export_to_jsonl(results, output_file)
                
            else:
                print(f"⚠️  Неподдерживаемый формат: {fmt}")
                
        except Exception as e:
            print(f"⚠️  Не удалось экспортировать в {fmt.upper()}: {e}")
    
    return exported_files

def generate_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Генерирует статистику по результатам классификации.
    
    Args:
        results: Список словарей с результатами
        
    Returns:
        Dict[str, Any]: Статистика
    """
    successful = [r for r in results if r.get('processed', False)]
    failed = [r for r in results if not r.get('processed', False)]
    
    # Статистика по категориям
    category_stats = {}
    confidence_scores = []
    
    for result in successful:
        if result.get('categories'):
            top_category = result['categories'][0][0]
            top_score = result['categories'][0][1]
            
            category_stats[top_category] = category_stats.get(top_category, 0) + 1
            confidence_scores.append(top_score)
    
    # Сортируем категории по частоте
    sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    
    stats = {
        "total_emails": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": f"{(len(successful) / len(results) * 100):.1f}%" if results else "0%",
        "top_categories": dict(sorted_categories[:10]),  # Топ-10 категорий
        "confidence": {
            "average": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            "min": min(confidence_scores) if confidence_scores else 0,
            "max": max(confidence_scores) if confidence_scores else 0
        } if confidence_scores else {}
    }
    
    return stats

def print_stats(stats: Dict[str, Any]):
    """
    Выводит статистику в консоль.
    
    Args:
        stats: Словарь со статистикой
    """
    print(f"\n📊 СТАТИСТИКА КЛАССИФИКАЦИИ:")
    print(f"   📧 Всего писем: {stats['total_emails']}")
    print(f"   ✅ Успешно обработано: {stats['successful']}")
    print(f"   ❌ Ошибок: {stats['failed']}")
    print(f"   🎯 Успешность: {stats['success_rate']}")
    
    if 'confidence' in stats and stats['confidence']:
        conf = stats['confidence']
        print(f"   📈 Уверенность классификации:")
        print(f"      • Средняя: {conf['average']:.3f}")
        print(f"      • Минимальная: {conf['min']:.3f}")
        print(f"      • Максимальная: {conf['max']:.3f}")
    
    if stats['top_categories']:
        print(f"   🏷️  Топ категории:")
        for category, count in stats['top_categories'].items():
            percentage = (count / stats['successful']) * 100 if stats['successful'] > 0 else 0
            print(f"      • {category}: {count} ({percentage:.1f}%)")

# Пример использования (для тестирования)
if __name__ == "__main__":
    # Тестовые данные
    test_results = [
        {
            "filename": "test1.eml",
            "subject": "Тестовое письмо",
            "categories": [("Финансы", 0.85), ("Отчеты", 0.45)],
            "processed": True,
            "confidence": 0.85
        }
    ]
    
    # Экспорт в разные форматы
    files = export_results(
        test_results,
        output_dir="../data_output",
        formats=['json', 'csv', 'jsonl']
    )
    
    print(f"\n📁 Экспортированные файлы: {files}")
    
    # Генерация статистики
    stats = generate_stats(test_results)
    print_stats(stats)