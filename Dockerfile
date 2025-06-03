FROM python:3.10

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Устанавливаем необходимые зависимости для сборки пакетов
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Запускаем бота при старте контейнера
CMD ["python", "main.py"]