# test.py - диагностика модели
from sentence_transformers import SentenceTransformer
import numpy as np

print("1. Тест загрузки модели...")
try:
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("   ✅ Модель загружена")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    exit(1)

print("2. Тест кодирования текста...")
try:
    text = "Техническая поддержка системы"
    emb = model.encode(text)
    print(f"   ✅ Эмбеддинг создан")
    print(f"   📊 Shape: {emb.shape}")
    print(f"   📊 Min: {emb.min():.6f}")
    print(f"   📊 Max: {emb.max():.6f}")
    print(f"   📊 Mean: {emb.mean():.6f}")
    print(f"   📊 Std: {emb.std():.6f}")
    
    # Проверка на NaN/Inf
    has_nan = np.isnan(emb).any()
    has_inf = np.isinf(emb).any()
    print(f"   🔍 NaN в эмбеддинге: {has_nan}")
    print(f"   🔍 Inf в эмбеддинге: {has_inf}")
    
except Exception as e:
    print(f"   ❌ Ошибка кодирования: {e}")
    exit(1)

print("3. Тест косинусного сходства...")
try:
    from sentence_transformers import util
    
    texts = ["Техническая поддержка", "Финансовые операции", "Билет на поезд"]
    embs = model.encode(texts)
    
    # Вычисляем сходства
    similarities = util.cos_sim(embs[0], embs[1:])
    print(f"   ✅ Сходства вычислены")
    print(f"   📊 Similarity 0-1: {similarities[0][0]:.6f}")
    print(f"   📊 Similarity 0-2: {similarities[0][1]:.6f}")
    
    # Проверка на NaN/Inf в similarities
    similarities_np = similarities.numpy()
    has_nan = np.isnan(similarities_np).any()
    has_inf = np.isinf(similarities_np).any()
    print(f"   🔍 NaN в сходствах: {has_nan}")
    print(f"   🔍 Inf в сходствах: {has_inf}")
    
except Exception as e:
    print(f"   ❌ Ошибка вычисления сходства: {e}")
    exit(1)

print("4. Тест ваших категорий...")
try:
    categories = [
        "Техническая поддержка. Техническая поддержка, клиенты, сотрудники",
        "Финансовые операции. Финансовые операции, чеки, счета, оплата",
        "Транспорт и путешествия. Транспорт, путешествия, билеты, отели"
    ]
    
    category_embs = model.encode(categories)
    print(f"   ✅ Эмбеддинги категорий созданы")
    print(f"   📊 Shape категорий: {category_embs.shape}")
    
    # Сходство с тестовым текстом
    test_text = "Ж/д билет из Москвы в Псков"
    test_emb = model.encode(test_text)
    sims = util.cos_sim(test_emb, category_embs)[0]
    
    print(f"   📊 Сходства с '{test_text}':")
    for i, sim in enumerate(sims):
        print(f"      {categories[i][:30]}...: {sim:.6f}")
        
except Exception as e:
    print(f"   ❌ Ошибка теста категорий: {e}")

print("\n✅ Диагностика завершена!")