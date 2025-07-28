# Image de base officielle Python
FROM python:3.11-slim

# Empêche Python de créer des fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définir le dossier de travail
WORKDIR /app

# Copier les dépendances
COPY requirements.txt /app/

# Installer les dépendances
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copier tout le code source dans le conteneur
COPY . /app/

# Exposer le port pour Gunicorn
EXPOSE 8000

# Commande par défaut (surchargée dans docker-compose)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]