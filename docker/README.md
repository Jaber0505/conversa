# 🐳 Configuration Docker - Conversa

Ce répertoire contient la configuration Docker pour exécuter Conversa en développement et en production.

## 📁 Structure

```
docker/
├── compose.dev.yml           # Docker-compose développement
├── Dockerfile.backend         # Image backend dev
├── Dockerfile.backend.prod    # Image backend production (multi-stage)
├── Dockerfile.frontend        # Image frontend dev
├── Dockerfile.frontend.prod   # Image frontend production (multi-stage + nginx)
├── .env.example               # Template variables d'environnement
├── .env.dev                   # Environnement développement (gitignored)
├── nginx/
│   └── default.conf           # Config Nginx pour frontend (SPA + proxy API)
└── pgadmin/
    └── servers.json           # Serveurs PgAdmin pré-configurés
```

## 🚀 Démarrage Rapide

### Développement

1. **Copier le fichier d'environnement :**
   ```bash
   cp docker/.env.example docker/.env.dev
   # Éditer .env.dev avec vos valeurs
   ```

2. **Démarrer tous les services :**
   ```bash
   docker compose -f docker/compose.dev.yml up -d
   ```

3. **Accéder aux services :**
   - Frontend : http://localhost:4200
   - API Backend : http://localhost:8000/api/v1/
   - Documentation Swagger : http://localhost:8000/api/docs/
   - PgAdmin : http://localhost:5050 (admin@conversa.be / admin123)

4. **Exécuter les migrations :**
   ```bash
   docker compose -f docker/compose.dev.yml exec backend python manage.py migrate
   ```

5. **Créer un superutilisateur :**
   ```bash
   docker compose -f docker/compose.dev.yml exec backend python manage.py createsuperuser
   ```

6. **Charger les fixtures (optionnel) :**
   ```bash
   docker compose -f docker/compose.dev.yml exec backend python manage.py loaddata languages partners
   ```

### Production

Le déploiement en production utilise des images séparées et est typiquement déployé sur Render.com :
- **Backend** : Déployé comme Web Service avec `Dockerfile.backend.prod`
- **Frontend** : Déployé comme Static Site avec nginx
- **Base de données** : PostgreSQL externe (Render PostgreSQL ou similaire)

Voir `DEPLOYMENT.md` pour le guide de déploiement en production.

## 🏗️ Architecture

### Stack Développement

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │    Backend      │
│  Angular 18     │────▶│   Django 4.2    │
│  Port: 4200     │     │   Port: 8000    │
└─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │  Port: 5432  │
                        └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   PgAdmin    │
                        │  Port: 5050  │
                        └──────────────┘
```

### Stack Production

```
┌─────────────────────┐
│  Nginx (Frontend)   │
│  - Sert le SPA      │
│  - Proxy vers /api/ │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│  Gunicorn+Uvicorn   │
│  Django ASGI        │
│  (Render.com)       │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│  PostgreSQL         │
│  (Render DB)        │
└─────────────────────┘
```

## 🔧 Détails des Services

### Service Backend

**Développement (`Dockerfile.backend`) :**
- Image de base : `python:3.11-slim`
- Auto-reload activé (volume monté)
- Mode debug ON
- Exécute le serveur de dev Django

**Production (`Dockerfile.backend.prod`) :**
- Build multi-stage (builder + runtime)
- Image runtime minimale
- Wheels Python pré-compilés
- Workers Gunicorn + Uvicorn (ASGI)
- Endpoint health check : `/healthz`

**Variables d'environnement :** Voir `.env.example`

### Service Frontend

**Développement (`Dockerfile.frontend`) :**
- Image de base : `node:20-alpine`
- Hot-reload activé
- Serveur de dev Angular avec live reload

**Production (`Dockerfile.frontend.prod`) :**
- Build multi-stage :
  - Stage 1 : Build de l'app Angular (`ng build --prod`)
  - Stage 2 : Servir avec Nginx
- Assets statiques optimisés
- Compression Gzip activée
- Headers de sécurité configurés

### Service Base de données (Dev uniquement)

- Image : `postgres:16-alpine`
- Volume : `pgdata` (stockage persistant)
- Health check : `pg_isready`
- Identifiants par défaut (dev uniquement) :
  - Utilisateur : `postgres`
  - Mot de passe : `postgres`
  - Base de données : `conversa_db`

⚠️ **Production :** Utiliser une base PostgreSQL managée (Render, AWS RDS, etc.)

### Service PgAdmin (Dev uniquement)

- Image : `dpage/pgadmin4:8`
- Pré-configuré avec PostgreSQL local
- Identifiants par défaut :
  - Email : `admin@conversa.be`
  - Mot de passe : `admin123`

## 🔒 Bonnes Pratiques de Sécurité

### ✅ Ce qui est implémenté

1. **Multi-stage builds** : ✅ Utilisé dans les Dockerfiles de production
2. **Images de base minimales** : ✅ Alpine Linux, Python slim
3. **Pas de secrets dans les images** : ✅ Tous les secrets via variables d'environnement
4. **Health checks** : ✅ Configuré pour la base de données
5. **Headers de sécurité** : ✅ Nginx configuré avec headers de sécurité
6. **Server tokens off** : ✅ Version nginx masquée
7. **Compression Gzip** : ✅ Activée pour les assets statiques

### ⚠️ Recommandations

#### 1. Ajouter un utilisateur non-root (Production)

**Actuellement :** Les containers s'exécutent en tant que root
**Recommandé :** Ajouter un utilisateur non-root dans les Dockerfiles de production

```dockerfile
# Ajouter dans Dockerfile.backend.prod après COPY backend/
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django
```

```dockerfile
# Dockerfile.frontend.prod utilise déjà l'utilisateur nginx par défaut - ✅ OK
```

#### 2. Scanner les images pour les vulnérabilités

```bash
# Installer trivy
# Scanner l'image backend
docker build -t conversa-backend:latest -f docker/Dockerfile.backend.prod .
trivy image conversa-backend:latest

# Scanner l'image frontend
docker build -t conversa-frontend:latest -f docker/Dockerfile.frontend.prod .
trivy image conversa-frontend:latest
```

#### 3. Utiliser Docker Secrets (Production)

Pour la production, considérer l'utilisation de Docker secrets ou d'un gestionnaire de secrets :
- Render : Variables d'environnement (chiffrées au repos)
- AWS : AWS Secrets Manager
- Kubernetes : Kubernetes Secrets

## 📊 Optimisation des Performances

### Backend

**Configuration Gunicorn** (`gunicorn.conf.py`) :
- Workers : Variable `WORKERS` (défaut : 2)
- Classe de worker : `uvicorn.workers.UvicornWorker` (ASGI)
- Threads : Variable `THREADS` (défaut : 4)
- Timeout : 60s
- Keep-alive : Activé

**Calcul recommandé :**
```
Workers = (2 x Cœurs CPU) + 1
Exemple : 2 cœurs CPU → 5 workers
```

### Frontend

**Optimisation Nginx :**
- Compression Gzip : ✅ Activée
- Cache des assets statiques : ✅ 1 an pour les fichiers avec empreinte
- HTML no-cache : ✅ Évite le SPA obsolète
- Client max body : 10MB

## 🐛 Dépannage

### Le backend ne démarre pas

```bash
# Vérifier les logs
docker compose -f docker/compose.dev.yml logs backend

# Problèmes courants :
# 1. Base de données pas prête → Attendre le health check
# 2. Migrations nécessaires → Exécuter : docker compose exec backend python manage.py migrate
# 3. Conflit de port → Changer le port dans compose.dev.yml
```

### Connexion à la base de données refusée

```bash
# S'assurer que la base de données est en bonne santé
docker compose -f docker/compose.dev.yml ps

# Devrait afficher le statut "healthy" pour le service db
# Sinon, vérifier les logs :
docker compose -f docker/compose.dev.yml logs db
```

### Le frontend ne peut pas joindre le backend

**Développement :**
- Vérifier les paramètres CORS dans `backend/config/settings/dev.py`
- S'assurer que `DJANGO_CORS_ALLOWED_ORIGINS` inclut `http://localhost:4200`

**Production :**
- Vérifier la configuration du proxy nginx dans `nginx/default.conf`
- Vérifier l'URL du backend dans la directive `proxy_pass`

### PgAdmin ne peut pas se connecter à la base de données

1. S'assurer que la base de données fonctionne :
   ```bash
   docker compose -f docker/compose.dev.yml ps db
   ```

2. Vérifier la configuration dans `docker/pgadmin/servers.json`

3. Recréer le container PgAdmin :
   ```bash
   docker compose -f docker/compose.dev.yml rm pgadmin
   docker compose -f docker/compose.dev.yml up -d pgadmin
   ```

## 🔄 Commandes Courantes

### Reconstruire les containers

```bash
# Tout reconstruire
docker compose -f docker/compose.dev.yml up --build

# Reconstruire un service spécifique
docker compose -f docker/compose.dev.yml up --build backend
```

### Voir les logs

```bash
# Tous les services
docker compose -f docker/compose.dev.yml logs -f

# Service spécifique
docker compose -f docker/compose.dev.yml logs -f backend
```

### Exécuter des commandes dans un container

```bash
# Shell Django
docker compose -f docker/compose.dev.yml exec backend python manage.py shell

# Exécuter les tests
docker compose -f docker/compose.dev.yml exec backend python manage.py test

# Créer une migration
docker compose -f docker/compose.dev.yml exec backend python manage.py makemigrations
```

### Nettoyer

```bash
# Arrêter tous les services
docker compose -f docker/compose.dev.yml down

# Arrêter et supprimer les volumes (⚠️ supprime la base de données)
docker compose -f docker/compose.dev.yml down -v

# Supprimer toutes les images
docker compose -f docker/compose.dev.yml down --rmi all
```

## 📝 Variables d'Environnement

Voir `.env.example` pour la liste complète des variables d'environnement.

**Variables critiques :**
- `SECRET_KEY` : Secret Django (générer avec `get_random_secret_key()`)
- `DJANGO_ALLOWED_HOSTS` : Hosts autorisés séparés par des virgules
- `DJANGO_STRIPE_SECRET_KEY` : Clé de test Stripe (doit commencer par `sk_test_`)
- `DJANGO_DB_PASSWORD` : Mot de passe de la base de données (changer en production !)

## 🚀 Déploiement en Production

**Docker Compose n'est pas utilisé en production.**

Les services sont déployés séparément :
1. **Backend** : Render Web Service (build natif)
2. **Frontend** : Render Static Site (nginx)
3. **Base de données** : Render PostgreSQL

Voir `../DEPLOYMENT.md` pour le guide complet de déploiement en production.

## 📚 Ressources Additionnelles

- [Bonnes Pratiques Django Docker](https://docs.docker.com/samples/django/)
- [Déploiement Gunicorn](https://docs.gunicorn.org/en/stable/deploy.html)
- [Headers de Sécurité Nginx](https://securityheaders.com/)
- [Bonnes Pratiques de Sécurité Docker](https://docs.docker.com/develop/security-best-practices/)

## 🆘 Support

Pour les problèmes ou questions :
1. Consulter la documentation existante
2. Vérifier les logs : `docker compose logs`
3. Ouvrir une issue sur GitHub

---

**Dernière mise à jour :** Octobre 2025
**Mainteneur :** Équipe Conversa
