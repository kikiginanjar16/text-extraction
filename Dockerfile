FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    file \
    libmagic1 \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --upgrade pip && pip install .

COPY .env.example ./.env.example

EXPOSE 8873

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8873"]
