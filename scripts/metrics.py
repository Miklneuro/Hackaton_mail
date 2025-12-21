import json
import os
from collections import Counter
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

def calculate_metrics(results: list):
    """Рассчитывает метрики классификации."""
    
    # Подготовка данных для метрик
    y_true = []
    y_pred = []
    
    for result in results:
        if not result.get('processed', False):
            continue
        
        # Извлекаем истинную категорию из имени файла
        from utils import extract_true_category_from_filename
        filename = result.get('filename', '')
        
        # Если файл без имени - ошибка, пропускаем
        if not filename:
            print(f"⚠️ ОШИБКА: Обработанный файл без имени! Пропускаем.")
            continue
        
        # Получаем истинную категорию
        true_category = extract_true_category_from_filename(filename)
        
        # Добавляем истинную метку (без проверки if true_category)
        y_true.append(true_category)
        
        # Берем предсказанную категорию (топ-1) ТОЧНО как из classifier.py
        # Без присвоения "Другое"
        predicted_category = result['categories'][0][0]  # Берем первую категорию как есть
        y_pred.append(predicted_category)
    
    if len(y_true) == 0:
        print("⚠️ Нет данных для расчета метрик")
        return None
    
    # Расчет метрик
    print("\n" + "="*60)
    print("📊 МЕТРИКИ КЛАССИФИКАЦИИ")
    print("="*60)
    
    accuracy = accuracy_score(y_true, y_pred)
    print(f"📈 Accuracy (Точность): {accuracy:.4f}")
    
    print("\n📋 Classification Report:")
    print("-" * 40)
    
    # Генерируем classification report
    report = classification_report(y_true, y_pred, output_dict=False, zero_division=0)
    print(report)
    
    # Confusion matrix
    print("\n🎯 Confusion Matrix:")
    print("-" * 40)
    
    # Получаем уникальные классы
    classes = sorted(set(y_true + y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    
    # Выводим confusion matrix
    print("Классы:", classes)
    print("Матрица:")
    for i in range(len(classes)):
        print(f"{classes[i]:<25}: {cm[i]}")
    
    # Детальная статистика по классам
    print("\n📊 Детальная статистика по классам:")
    print("-" * 40)
    
    true_counts = Counter(y_true)
    pred_counts = Counter(y_pred)
    
    print("Истинное распределение:")
    for category, count in true_counts.most_common():
        print(f"  {category:<25}: {count:>3} ({count/len(y_true):.1%})")
    
    print("\nПредсказанное распределение:")
    for category, count in pred_counts.most_common():
        print(f"  {category:<25}: {count:>3} ({count/len(y_pred):.1%})")
    
    # Полный classification report в виде словаря
    report_dict = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    
    metrics_data = {
        'accuracy': accuracy,
        'y_true': y_true,
        'y_pred': y_pred,
        'classes': classes,
        'confusion_matrix': cm.tolist(),
        'classification_report': report_dict,
        'true_distribution': dict(true_counts),
        'predicted_distribution': dict(pred_counts)
    }
    
    return metrics_data

def save_metrics_to_file(metrics_data: dict, output_dir: str, filename_prefix: str = 'metrics'):
    """Сохраняет метрики в JSON файл."""
    if not metrics_data:
        return None
    
    metrics_file = os.path.join(output_dir, f"{filename_prefix}.json")
    
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Метрики сохранены: {metrics_file}")
    return metrics_file