# Configuration Cron Job sur Render.com

## Pourquoi ?

L'appel à `BookingService.auto_expire_bookings()` a été retiré de `BookingViewSet.list()` car :
- Cause des UPDATEs globaux à chaque requête utilisateur
- Ajoute de la latence inutile
- Peut causer des race conditions

À la place, utilisez un cron job Render.

## Configuration sur Render.com (Free tier compatible!)

### 1. Dans le Dashboard Render

1. Sélectionnez votre service web Django
2. Cliquez sur **"Cron Jobs"** dans le menu
3. Cliquez **"Add Cron Job"**

### 2. Configuration du Cron Job

```yaml
Name: Expire Pending Bookings
Command: python manage.py expire_bookings
Schedule: */5 * * * *
```

**Explication du schedule** :
- `*/5 * * * *` = toutes les 5 minutes
- `*/10 * * * *` = toutes les 10 minutes (recommandé pour économiser les ressources)
- `0 * * * *` = toutes les heures

### 3. Variables d'environnement

Assurez-vous que les variables suivantes sont définies dans Render :
- `DJANGO_SETTINGS_MODULE=config.settings.prod`
- `DATABASE_URL` (automatiquement définie par Render)
- Toutes les autres variables de votre app

### 4. Tester localement

```bash
# Test du management command
python manage.py expire_bookings

# Devrait afficher :
# Starting booking expiration process...
# Successfully expired X booking(s)
```

## Alternative : Script Shell (si cron jobs ne fonctionnent pas)

Si Render ne supporte pas les cron jobs dans le free tier, utilisez un service externe gratuit :

### Option A : GitHub Actions

Créez `.github/workflows/expire_bookings.yml` :

```yaml
name: Expire Bookings
on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes

jobs:
  expire:
    runs-on: ubuntu-latest
    steps:
      - name: Call Render webhook
        run: |
          curl -X POST https://your-app.onrender.com/api/v1/cron/expire-bookings \
               -H "Authorization: Bearer ${{ secrets.CRON_TOKEN }}"
```

### Option B : Render Background Workers

Si vous avez besoin de plus de contrôle, créez un "Background Worker" Render qui exécute :

```bash
# start_worker.sh
while true; do
    python manage.py expire_bookings
    sleep 300  # 5 minutes
done
```

## Monitoring

Le command log dans :
- Render Dashboard > Logs
- Cherchez "Successfully expired X booking(s)"

## Troubleshooting

**Erreur "command not found"** :
- Vérifiez que `manage.py` est à la racine de votre projet
- Commande complète : `cd backend && python manage.py expire_bookings`

**Timeout** :
- Augmentez l'intervalle (ex: 10 minutes au lieu de 5)
- Optimisez la requête dans `BookingService.auto_expire_bookings()`
