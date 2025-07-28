**Conversa** est une plateforme web qui permet d’organiser ou rejoindre des événements linguistiques immersifs dans des bars à Bruxelles.  
En petit groupe, les participants pratiquent une langue via des jeux collaboratifs.  

Ce projet est développé en **Django + React** dans le cadre d’un **Travail de Fin d’Études (TFE)** à l’**ICC – Bachelier Informatique**.

---

## Tech Stack

- Backend : Django 5 (Python)
- Frontend : React 18 (Create React App)
- Base de données : PostgreSQL
- Conteneurisation : Docker + Docker Compose
- Déploiement prévu : GitHub Actions + hébergement cloud

---

## Lancer le projet en local (Docker)

### Prérequis

- Docker & Docker Compose installés
- Fichier `.env` présent dans le dossier `backend/` (voir `.env.example`)

---

### Démarrer tous les services

#### Windows PowerShell
```powershell
.\start-dev.ps1

### Arrêter les services
```powershell
.\stop-dev.ps1

