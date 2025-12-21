import sys
import os
import importlib
from pathlib import Path

print("DEBUG: Скрипт начал выполнение.")

# Получаем корень проекта
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
print(f"📁 Корень проекта: {PROJECT_ROOT}")

# Список обязательных библиотек с правильными именами импорта
REQUIRED_LIBRARIES = [
    "sentence_transformers",
    "pandas",
    "numpy",
    ("pdfminer", "pdfminer.six"),      # Импортируется как pdfminer
    ("docx", "python-docx"),           # Импортируется как docx
    "openpyxl",
    "tldextract",
    ("bs4", "beautifulsoup4"),         # Импортируется как bs4
    "extract_msg",
]

# Проверка наличия библиотек
def check_libraries():
    print("\n🔍 Проверка наличия библиотек...")
    all_available = True
    for lib in REQUIRED_LIBRARIES:
        try:
            if isinstance(lib, tuple):
                import_name, pip_name = lib
                importlib.import_module(import_name)
                print(f"   ✅ {pip_name} доступна (импортируется как {import_name})")
            else:
                importlib.import_module(lib)
                print(f"   ✅ {lib} доступна")
        except ImportError as e:
            if isinstance(lib, tuple):
                print(f"   ❌ {lib[1]} НЕДОСТУПНА: {e}")
            else:
                print(f"   ❌ {lib} НЕДОСТУПНА: {e}")
            all_available = False
    return all_available

# Проверка структуры проекта
def check_project_structure():
    print("\n📂 Проверка структуры проекта...")
    required_folders = ["data_input", "data_output", "categories", "logs"]
    all_folders_exist = True
    for folder in required_folders:
        folder_path = os.path.join(PROJECT_ROOT, folder)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            print(f"   ✅ Папка {folder} существует: {folder_path}")
        else:
            print(f"   ❌ Папка {folder} НЕДОСТУПНА: {folder_path}")
            all_folders_exist = False
    return all_folders_exist

# Проверка файла категорий
def check_categories_file():
    print("\n📝 Проверка файла категорий...")
    categories_file_path = os.path.join(PROJECT_ROOT, "categories", "new_cats.txt")
    print(f"   🔍 Проверяется путь: {categories_file_path}")
    print(f"   📁 Существует ли путь? {os.path.exists(categories_file_path)}")
    print(f"   📄 Это файл? {os.path.isfile(categories_file_path)}")

    if os.path.exists(categories_file_path) and os.path.isfile(categories_file_path):
        print(f"   ✅ Файл категорий найден: {categories_file_path}")
        return True
    else:
        print(f"   ❌ Файл категорий НЕДОСТУПЕН: {categories_file_path}")
        return False

# Проверка наличия тестовых данных
def check_test_data():
    print("\n📧 Проверка тестовых данных...")
    input_folder = os.path.join(PROJECT_ROOT, "data_input")
    if os.path.exists(input_folder):
        files = os.listdir(input_folder)
        eml_files = [f for f in files if f.endswith('.eml')]
        msg_files = [f for f in files if f.endswith('.msg')]
        print(f"   📁 Всего файлов в data_input: {len(files)}")
        print(f"   📨 .eml файлов: {len(eml_files)}")
        print(f"   📨 .msg файлов: {len(msg_files)}")
        
        if len(eml_files) == 0 and len(msg_files) == 0:
            print("   ⚠️  В папке data_input нет .eml или .msg файлов!")
            print("   💡 Добавьте тестовые письма для работы классификатора")
            return False
        return True
    else:
        print(f"   ❌ Папка data_input не существует: {input_folder}")
        return False

# Основная функция проверки
def main():
    print("\n🚀 Запуск проверки окружения...\n")

    # Проверка Python версии
    print(f"🐍 Python версия: {sys.version}")
    if sys.version_info < (3, 8):
        print("   ❌ Требуется Python версии 3.8 или выше!")
        sys.exit(1)

    # Проверка библиотек
    libraries_ok = check_libraries()

    # Проверка структуры проекта
    folders_ok = check_project_structure()

    # Проверка файла категорий
    categories_ok = check_categories_file()

    # Проверка тестовых данных
    data_ok = check_test_data()

    # Итоговый отчет
    print("\n" + "="*50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")
    print("="*50)
    
    if libraries_ok and folders_ok and categories_ok:
        print("✅ Все основные проверки пройдены успешно!")
        print(f"📦 Установлено библиотек: {len(REQUIRED_LIBRARIES)}")
        
        if not data_ok:
            print("\n⚠️  ПРЕДУПРЕЖДЕНИЕ:")
            print("   Классификатор может работать, но для тестирования")
            print("   добавьте .eml или .msg файлы в папку data_input/")
        
        print("\n🎯 Следующие шаги:")
        print("   1. Добавьте письма в data_input/ (если еще нет)")
        print("   2. Запустите: python scripts/main.py")
        print("   3. Проверьте результаты в data_output/")
    else:
        print("❌ Обнаружены проблемы:")
        if not libraries_ok:
            print("   - Не все библиотеки установлены")
        if not folders_ok:
            print("   - Не хватает папок проекта")
        if not categories_ok:
            print("   - Файл категорий не найден")
        
        print("\n🔧 Рекомендации:")
        print("   - Установите недостающие библиотеки: pip install <библиотека>")
        print("   - Создайте недостающие папки")
        print("   - Проверьте файл categories/new_cats.txt")

if __name__ == "__main__":
    main()