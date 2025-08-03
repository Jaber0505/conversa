#!/bin/sh
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh

COPY . /app/

ENTRYPOINT ["/app/entrypoint.sh"]
