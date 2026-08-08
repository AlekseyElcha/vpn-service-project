FROM python:3.14-slim

# Устанавливаем системные зависимости (если понадобятся для asyncpg или др.)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
RUN pip install uv

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости на уровне системы
RUN uv sync --frozen --no-dev

# Копируем весь проект
COPY . .

# Команда для запуска бэкенда
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
