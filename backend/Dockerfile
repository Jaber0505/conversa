FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh
COPY . /app/

ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8000