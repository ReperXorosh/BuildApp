FROM python:3.13

WORKDIR /app

# Сначала копируем только requirements.txt
COPY requirements.txt /app/

# Ставим зависимости (слой кешируется, если requirements.txt не изменился)
RUN apt-get update && apt-get install -y gcc \
    && pip install --no-cache-dir -r requirements.txt

# Теперь уже код приложения
COPY . /app/

CMD ["gunicorn", "__init__:app"]
