# Conversa

**Conversa** est une plateforme web permettant d’organiser ou de rejoindre des événements linguistiques immersifs dans des bars à Bruxelles.  
En petits groupes, les participants pratiquent une langue étrangère à travers des jeux collaboratifs conçus pour favoriser l’expression orale et l’échange.

Ce projet est développé en **Django + React** dans le cadre d’un **Travail de Fin d’Études (TFE)** à l’**Institut des Carrières Commerciales (ICC)** — Bachelier en Informatique de gestion.

---

## Stack technique

- Backend : Django 5 (Python)  
- Frontend : React 18 (Create React App)  
- Base de données : PostgreSQL  
- Conteneurisation : Docker + Docker Compose  
- Déploiement : Render.com

---

## Lancer le projet en local (via Docker)

### Prérequis

- Avoir Docker et Docker Compose installés  
- Créer un fichier `.env` dans le dossier `backend` avec les variables d’environnement nécessaires (voir exemple plus bas)

---

### Démarrer les services

Depuis la racine du projet, exécuter le script suivant :  
scripts/start-dev.ps1

Ce script lance les services suivants :  
- PostgreSQL (db)  
- Django backend (backend)  
- React frontend (frontend)  
- Interface pgAdmin (pgadmin)

---

### Arrêter les services

Utiliser le script suivant :  
scripts/stop-dev.ps1

---

### Rebuild complet (backend + frontend)

Utiliser le script suivant :  
scripts/rebuild-dev.ps1

---

## Exemple de fichier `.env` pour le backend

Contenu recommandé du fichier `backend/.env` :

ENV_MODE=local  
DEBUG=True  
SECRET_KEY=django-insecure-xxxxxxx-REPLACE-THIS-xxxxxxxx  
ALLOWED_HOSTS=localhost,127.0.0.1  
DJANGO_DB_ENGINE=django.db.backends.postgresql  
DJANGO_DB_NAME=conversadb  
DJANGO_DB_USER=postgres  
DJANGO_DB_PASSWORD=postgres  
DJANGO_DB_HOST=db  
DJANGO_DB_PORT=5432

---

## Structure du projet

Conversa/  
├── backend/            -> application Django (API)  
├── frontend/           -> application React (interface utilisateur)  
├── pgadmin/            -> configuration pour pgAdmin  
├── scripts/            -> scripts PowerShell pour automatiser le dev  
├── docker-compose.yml  -> configuration multi-service Docker  
└── README.md

---

## Auteur

Projet réalisé par **Jaber Boudouh**  
dans le cadre d’un **Travail de Fin d’Études** à l’**ICC – Institut des Carrières Commerciales**  
Bachelier en Informatique de gestion – année académique 2024–2025
