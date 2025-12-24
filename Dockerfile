# Используем официальный образ Python 3.9
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем requirements.txt (если есть)
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все выделенные папки и файлы
COPY categories/ ./categories/
COPY data_input/ ./data_input/
COPY data_output/ ./data_output/
COPY logs/ ./logs/
COPY model_cache/ ./model_cache/
COPY scripts/ ./scripts/
COPY logo.jpg ./logo.jpg

# Указываем команду запуска (замените на вашу основную скрипт-точку входа)
# Пример: если ваш главный скрипт — это scripts/main.py
CMD ["python", "scripts/main.py"]