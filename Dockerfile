FROM python:3.13

WORKDIR /app

# Сначала копируем только requirements.txt
COPY requirements.txt /app/

# Ставим зависимости (слой кешируется, если requirements.txt не изменился)
RUN apt-get update && apt-get install -y gcc \
    && pip install --no-cache-dir -r requirements.txt

# Теперь уже код приложения
COPY . /app/

# Очищаем кэш Python байт-кода для гарантии использования нового кода
RUN find /app -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
RUN find /app -name "*.pyc" -delete 2>/dev/null || true

CMD ["gunicorn", "-w", "4", "--threads", "2", "-b", "0.0.0.0:8080", "run:application", "--log-level", "info", "--access-logfile", "-"]
