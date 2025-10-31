# Déploiement Render Free - Guide Complet

Ce guide explique comment déployer Conversa sur Render Free Tier avec le module Audit optimisé.

---

## 🎯 Configuration Render (Dashboard)

### 1. Variables d'Environnement

Aller dans **Dashboard → Environment** et ajouter :

```bash
# Django
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=your-super-secret-key-here-min-50-chars
DEBUG=false
ALLOWED_HOSTS=your-app.onrender.com

# Database (auto-généré par Render)
DATABASE_URL=postgresql://...

# Audit - Mode Free Tier
RENDER_FREE_TIER=true

# Optionnel : Skip HTTP logs (économiser espace)
# AUDIT_SKIP_HTTP=true
```

### 2. Build Command

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### 3. Start Command

```bash
gunicorn config.wsgi:application --workers 2 --bind 0.0.0.0:$PORT
```

---

## 🔧 Configuration GitHub Secrets

Pour activer le cleanup automatique, ajouter ces secrets dans **GitHub → Settings → Secrets** :

### `RENDER_APP_URL`
```
https://your-app.onrender.com
```

### `ADMIN_TOKEN`

**Étape 1 : Créer un admin user**

```bash
# Localement ou via Render shell
docker exec conversa-backend python manage.py createsuperuser
# Email: admin@conversa.com
# Password: ***
```

**Étape 2 : Obtenir un JWT token**

```bash
curl -X POST https://your-app.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@conversa.com","password":"***"}'

# Réponse :
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",  # ← Copier ce token
  "refresh": "..."
}
```

**Étape 3 : Ajouter le token dans GitHub Secrets**

GitHub → Settings → Secrets → New repository secret

```
Name: ADMIN_TOKEN
Value: eyJ0eXAiOiJKV1QiLCJhbGc...  (le access token)
```

⚠️ **Important :** Les JWT tokens expirent (généralement 1-7 jours). Solutions :

**Option A : Token long-lived** (Recommandé)

```python
# config/settings/prod.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),  # 1 an pour GitHub Actions
    'REFRESH_TOKEN_LIFETIME': timedelta(days=730),
    ...
}
```

**Option B : Refresh automatique dans GitHub Actions**

Voir `.github/workflows/audit_cleanup.yml` (déjà inclus)

---

## 🚀 Activer GitHub Actions

### 1. Vérifier que le fichier existe

```
.github/workflows/audit_cleanup.yml
```

✅ Déjà créé ! Il s'exécutera automatiquement chaque dimanche à 3h du matin.

### 2. Tester manuellement

GitHub → Actions → Audit Cleanup → Run workflow

### 3. Vérifier les logs

GitHub → Actions → Dernière exécution

---

## 🧪 Tests Locaux (Docker)

### 1. Vérifier que l'audit fonctionne

```bash
# Démarrer Docker
docker-compose up -d

# Créer un admin
docker exec conversa-backend python manage.py createsuperuser

# Tester AuditService
docker exec conversa-backend python manage.py shell
>>> from audit.services import AuditService
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.first()
>>> log = AuditService.log_auth_login(user, ip='127.0.0.1')
>>> print(log)
[AUTH] login_success by user@example.com
>>> exit()

# Vérifier dans admin
http://localhost:8000/admin/audit/auditlog/
```

### 2. Tester le cleanup

```bash
# Dry run
docker exec conversa-backend python manage.py cleanup_old_audits --dry-run

# Vrai cleanup
docker exec conversa-backend python manage.py cleanup_old_audits
```

### 3. Tester les endpoints API

```bash
# Obtenir token admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@conversa.com","password":"***"}' \
  | jq -r '.access')

# Stats audit
curl -s http://localhost:8000/api/v1/audit/stats/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Cleanup via API
curl -s -X POST http://localhost:8000/api/v1/audit/cleanup/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

## 📊 Monitoring Render Free

### 1. Vérifier l'espace DB

```bash
# Render Shell (Dashboard → Shell)
python manage.py shell

>>> from django.db import connection
>>> with connection.cursor() as cursor:
...     cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
...     print(cursor.fetchone()[0])
12 MB  # ← Sur 256 MB disponibles

>>> # Taille table audit
>>> cursor.execute("SELECT pg_size_pretty(pg_total_relation_size('audit_auditlog'))")
>>> print(cursor.fetchone()[0])
3 MB
```

### 2. Stats via API

```bash
curl https://your-app.onrender.com/api/v1/audit/stats/ \
  -H "Authorization: Bearer $TOKEN"

# Réponse :
{
  "total_logs": 1523,
  "by_category": {
    "HTTP": 1200,
    "AUTH": 250,
    "EVENT": 50,
    "BOOKING": 20,
    "PAYMENT": 3
  },
  "by_level": {
    "INFO": 1400,
    "WARNING": 100,
    "ERROR": 23
  },
  "oldest_log": "2025-09-15T10:00:00Z",
  "newest_log": "2025-10-06T21:00:00Z",
  "table_size": "3 MB"
}
```

### 3. Dashboard Admin

```
https://your-app.onrender.com/admin/audit/auditlog/

Filtres disponibles :
- Category (HTTP, AUTH, EVENT, etc.)
- Level (INFO, WARNING, ERROR)
- Date
- User
```

---

## 🔄 Workflow de Développement

### Local (Dev)

```bash
# .env ou docker/.env.dev
RENDER_FREE_TIER=false  # ← Rétention complète (90j, 1an, 7ans)
DEBUG=true
```

### Render (Prod Free)

```bash
# Dashboard Environment
RENDER_FREE_TIER=true   # ← Rétention réduite (7j, 30j, 30j)
DEBUG=false
```

---

## ⚠️ Limitations & Solutions

### Problème 1 : DB Full (256 MB)

**Symptômes :**
```
django.db.utils.OperationalError: disk full
```

**Solutions immédiates :**

```bash
# 1. Cleanup urgent
curl -X POST https://your-app.onrender.com/api/v1/audit/cleanup/ \
  -H "Authorization: Bearer $TOKEN"

# 2. Réduire rétention à 7 jours partout
# Render Dashboard → Environment
AUDIT_RETENTION_HTTP=7
AUDIT_RETENTION_AUTH=7
AUDIT_RETENTION_BUSINESS=7

# 3. Désactiver logs HTTP
AUDIT_SKIP_HTTP=true

# 4. Redémarrer app
```

### Problème 2 : GitHub Actions ne fonctionne pas

**Vérifier :**

1. ✅ Secrets GitHub configurés (`RENDER_APP_URL`, `ADMIN_TOKEN`)
2. ✅ Token admin valide (pas expiré)
3. ✅ URL correcte (https, pas http)
4. ✅ Endpoint accessible : `curl https://your-app.onrender.com/api/v1/audit/stats/`

**Regénérer token si expiré :**

```bash
# Login pour nouveau token
curl -X POST https://your-app.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@conversa.com","password":"***"}' \
  | jq -r '.access'

# Copier dans GitHub Secrets
```

### Problème 3 : App freeze (Render Free spin down)

**Normal** : Render Free stoppe l'app après 15 min d'inactivité.

**Solutions :**
- ✅ Première requête = 30-60s (cold start)
- ✅ UptimeRobot ping gratuit (keep alive)
- ✅ Passer à Render Paid $7/mois (pas de spin down)

---

## 📈 Quand Migrer vers Paid ?

### Indicateurs :

- ✅ App utilisée régulièrement (>100 users)
- ⚠️ DB > 200 MB (proche de 256 MB)
- ⚠️ Cold starts gênent UX
- ✅ Besoin logs > 30 jours (compliance)
- ✅ Génère revenus ($20+/mois)

### Avantages Render Paid ($7/mois) :

- ✅ 1 GB DB (au lieu de 256 MB)
- ✅ Pas de spin down
- ✅ Backups automatiques
- ✅ Cron jobs natifs
- ✅ Rétention illimitée (7 ans business logs OK)

---

## ✅ Checklist Déploiement Final

### Render Dashboard

- [ ] Variables environnement configurées (`RENDER_FREE_TIER=true`, etc.)
- [ ] Build command correcte
- [ ] Start command correcte (gunicorn)
- [ ] DB PostgreSQL créée et connectée

### GitHub

- [ ] Secrets configurés (`RENDER_APP_URL`, `ADMIN_TOKEN`)
- [ ] Workflow `.github/workflows/audit_cleanup.yml` présent
- [ ] Tester manuellement : Actions → Run workflow

### Tests

- [ ] App accessible : `https://your-app.onrender.com/healthz` → "ok"
- [ ] Admin accessible : `https://your-app.onrender.com/admin/`
- [ ] Logs audit créés automatiquement (middleware actif)
- [ ] Endpoints audit fonctionnent (`/api/v1/audit/stats/`)
- [ ] Cleanup manuel OK : `POST /api/v1/audit/cleanup/`

### Monitoring

- [ ] Vérifier espace DB (< 200 MB)
- [ ] Vérifier stats audit via API
- [ ] Configurer alertes si > 200 MB (optionnel)

---

## 📞 Support

**Problèmes courants :**
- Voir `audit/RENDER_FREE_SETUP.md` (guide détaillé)
- Voir `audit/README.md` (documentation module)

**GitHub Actions logs :**
- GitHub → Actions → Dernière exécution

**Render logs :**
- Dashboard → Logs (live streaming)

---

**Dernière mise à jour :** 2025-10-06
**Compatible :** Render Free Tier ✅
