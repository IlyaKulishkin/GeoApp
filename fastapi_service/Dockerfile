FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY fastapi_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .

RUN useradd -m -u 1000 fastapi && chown -R fastapi:fastapi /app

USER fastapi

EXPOSE 8001
