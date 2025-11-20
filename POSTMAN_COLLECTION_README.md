# Collection Postman - Démonstration des Permissions Organisateur

## 📋 Vue d'ensemble

Cette collection Postman démontre les permissions spécifiques aux **organisateurs** dans l'API Conversa. Elle permet de tester et valider que certains endpoints sont accessibles uniquement par les organisateurs (et admins), mais PAS par les utilisateurs réguliers.

## 🎯 Objectif

Montrer clairement quels endpoints nécessitent les privilèges d'organisateur en testant les mêmes requêtes avec différents types d'utilisateurs :
- ✅ **Organisateur** : Accès autorisé
- ❌ **Utilisateur régulier** : Accès refusé (403 Forbidden)
- ⚠️ **Admin** : Accès autorisé (les admins ont accès à tout)

## 📦 Fichier de la collection

**Fichier** : `Conversa_Organizer_Permissions.postman_collection.json`

## 🚀 Installation et Configuration

### 1. Importer la collection dans Postman

1. Ouvrez Postman
2. Cliquez sur **Import** (en haut à gauche)
3. Sélectionnez le fichier `Conversa_Organizer_Permissions.postman_collection.json`
4. La collection sera ajoutée à votre workspace

### 2. Configurer l'URL de base

Après l'import, configurez l'URL :

1. Cliquez sur la collection "Conversa - Organizer Permissions Demo"
2. Allez dans l'onglet **Variables**
3. Configurez `base_url` :
   - Pour développement local : `http://localhost:8000`
   - Pour production : votre URL de production

### 3. ⚙️ SETUP AUTOMATIQUE - Exécuter la section "0. Setup"

**C'est tout!** La collection crée automatiquement tout le contexte nécessaire.

Exécutez **TOUTES les requêtes de la section "0. Setup"** dans l'ordre :

1. **Register Organizer User** → Crée `organizer.test@conversa.com`
2. **Register Regular User** → Crée `user.test@conversa.com`
3. **Login as Organizer** → Récupère le token
4. **Create Test Event** → Crée un événement (l'organisateur devient propriétaire, event_id sauvegardé)
5. **Login as Regular User** → Récupère le token
6. **Login as Admin** (optionnel) → Requiert création manuelle via `python manage.py createsuperuser`

#### Variables automatiquement créées :
- `organizer_email` = organizer.test@conversa.com
- `organizer_password` = TestPassword123!
- `organizer_token` = JWT token
- `regular_user_email` = user.test@conversa.com
- `regular_user_password` = TestPassword123!
- `regular_user_token` = JWT token
- `event_id` = ID de l'événement créé
- `admin_token` = JWT token (si admin créé manuellement)

#### Données de test utilisées pour la création des comptes :
- **Organisateur** : 30 ans, langue native: anglais (en), langue cible: français (fr)
- **Utilisateur régulier** : 25 ans, langue native: français (fr), langue cible: anglais (en)
- **Consentement RGPD** : `consent_given: true` pour les deux comptes

#### Données de test pour la création de l'événement :
- **partner** : 1 (ID du partenaire/venue - doit exister en BDD)
- **language** : 1 (ID de la langue - doit exister en BDD)
- **theme** : "Test Permissions Event"
- **difficulty** : "medium" (valeurs possibles: easy, medium, hard)
- **datetime_start** : "2025-01-15T19:00:00Z" (dans les 7 jours, min 3h à l'avance)
- **game_type** : "picture_description" (optionnel, valeurs: picture_description, word_association, debate, role_play)

#### Si les utilisateurs existent déjà
Pas de problème! La collection détecte si les utilisateurs existent déjà (erreur 400) et continue quand même.

## 📝 Structure de la Collection

### 0. Setup - Create Test Environment ⚙️
**SETUP AUTOMATIQUE** - Crée tout le contexte nécessaire :
1. **Register Organizer User** : Crée le compte organisateur
2. **Register Regular User** : Crée le compte utilisateur régulier
3. **Login as Organizer** : Récupère le token JWT
4. **Create Test Event** : Crée un événement (devient automatiquement organisateur)
5. **Login as Regular User** : Récupère le token JWT
6. **Login as Admin** : Récupère le token JWT (requiert création manuelle)

### 1. POST - Create Game (Organizer or Admin)
**Endpoint** : `POST /api/v1/games/create/`

Démontre que seuls les organisateurs (et admins) peuvent créer un jeu pour un événement.

**Permission** : `GameService._validate_organizer_permission()`
```python
if event.organizer_id != user.id and not user.is_staff:
    raise PermissionDenied("Only the event organizer can create games")
```

### 2. POST - Reveal Answer (Organizer or Admin)
**Endpoint** : `POST /api/v1/games/{id}/reveal-answer/`

Seul l'organisateur peut révéler la réponse de la question courante pendant une partie.

**Permission** : `GameService._validate_organizer_permission()`

### 3. POST - Next Question (Organizer or Admin)
**Endpoint** : `POST /api/v1/games/{id}/next-question/`

Seul l'organisateur peut avancer à la question suivante pendant une partie.

**Permission** : `GameService._validate_organizer_permission()`

### 4. PATCH - Update Event (Organizer ONLY - NOT Admin!)

**Endpoint** : `PATCH /api/v1/events/{id}/`

⚠️ **IMPORTANT** : Cet endpoint est le SEUL qui refuse l'accès aux admins!

Seul l'organisateur propriétaire peut modifier son événement. Même les admins (is_staff=True) reçoivent **403 Forbidden**.

**Permission** : `IsOrganizerOrReadOnly`
```python
return obj.organizer_id == request.user.id  # PAS d'exception pour is_staff!
```

**Champs modifiables** :
- `theme` : Thème de l'événement
- `difficulty` : Niveau (easy, medium, hard)
- `datetime_start` : Date/heure de début
- `game_type` : Type de jeu (picture_description, word_association, debate, role_play)
- `partner` : ID du partenaire (venue)
- `language` : ID de la langue
- `photo` : Image de l'événement (optionnel)

**Champs verrouillés** (read-only, non modifiables) :
- `title` : Auto-généré depuis partner.name
- `price_cents` : Prix fixe (700 cents = 7.00€)
- `address` : Auto-généré depuis partner.address
- `organizer` : Créateur de l'événement
- `max_participants`, `min_participants` : Limites de participants (fixées à 6 et 3)
- `status`, `published_at`, `cancelled_at` : État de l'événement
- Tous les champs calculés (_links, is_full, booked_seats, etc.)

**Tests inclus** :
- ✅ Organisateur → 200 OK
- ❌ Utilisateur régulier → 403 Forbidden
- ❌ **Admin → 403 Forbidden** (NOUVEAU!)

### 5. DELETE - Delete Event (Organizer or Admin)
**Endpoint** : `DELETE /api/v1/events/{id}/`

Seul l'organisateur peut supprimer son événement (si aucune réservation confirmée).

**Permission** : `IsOrganizerOrAdmin`
```python
return getattr(obj, "organizer_id", None) == getattr(request.user, "id", None)
```

### 6. POST - Cancel Event (Organizer or Admin)
**Endpoint** : `POST /api/v1/events/{id}/cancel/`

Seul l'organisateur peut annuler son événement (déclenche automatiquement les remboursements).

**Permission** : `IsOrganizerOrAdmin`

### 7. GET - Event Participants (Organizer Only)
**Endpoint** : `GET /api/v1/events/{id}/participants/`

Seul l'organisateur peut voir la liste complète des participants confirmés.

**Validation** : Vérification manuelle dans la view
```python
if event.organizer_id != request.user.id:
    raise PermissionDenied("Only organizer can view participants")
```

## 🧪 Comment utiliser la collection

### ⚡ GUIDE RAPIDE (3 étapes)

1. **Importez** la collection dans Postman
2. **Configurez** `base_url` = `http://localhost:8000` (dans Variables)
3. **Exécutez** toutes les requêtes de "0. Setup" dans l'ordre (1-6)

C'est tout! Vous êtes prêt à tester. 🎉

### Méthode 1 : Exécution manuelle

1. **Étape 1** : Exécutez TOUTES les requêtes de "0. Setup" dans l'ordre (1 → 6)
   - Vérifiez dans la console que vous voyez les ✅ messages de succès
   - Les tokens et l'event_id sont sauvegardés automatiquement

2. **Étape 2** : Pour chaque endpoint (sections 1-7), exécutez dans l'ordre :
   - ✅ La requête "AS ORGANIZER" (doit retourner 200/201)
   - ❌ La requête "AS REGULAR USER" (doit retourner 403)
   - ⚠️ La requête "AS ADMIN" si disponible (doit retourner 200/201 ou 403 pour PATCH)

### Méthode 2 : Collection Runner

1. Cliquez sur la collection
2. Cliquez sur **Run** (ou **Runner**)
3. Sélectionnez les dossiers que vous voulez tester
4. Cliquez sur **Run Conversa - Organizer Permissions Demo**
5. Observez les résultats des tests

## ✅ Tests automatiques intégrés

Chaque requête inclut des tests JavaScript qui valident automatiquement :

### Pour les requêtes "AS ORGANIZER"
```javascript
pm.test('Status code is 200/201', function () {
    pm.response.to.have.status(200); // ou 201 pour POST
});
```

### Pour les requêtes "AS REGULAR USER"
```javascript
pm.test('Status code is 403 Forbidden', function () {
    pm.response.to.have.status(403);
});
```

## 📊 Résultats attendus

| Endpoint | Organisateur | Utilisateur | Admin |
|----------|-------------|------------|-------|
| POST /games/create/ | ✅ 201 | ❌ 403 | ✅ 201 |
| POST /games/{id}/reveal-answer/ | ✅ 200 | ❌ 403 | ✅ 200 |
| POST /games/{id}/next-question/ | ✅ 200 | ❌ 403 | ✅ 200 |
| **PATCH /events/{id}/** | ✅ 200 | ❌ 403 | ❌ **403** ⚠️ |
| DELETE /events/{id}/ | ✅ 204 | ❌ 403 | ✅ 204 |
| POST /events/{id}/cancel/ | ✅ 200 | ❌ 403 | ✅ 200 |
| GET /events/{id}/participants/ | ✅ 200 | ❌ 403 | ✅ 200 |

⚠️ **IMPORTANT** : Notez que `PATCH /events/{id}/` est le **seul endpoint** qui refuse l'accès aux admins!

## ⚠️ Note importante : Admin vs Organizer

### Distinction entre les permissions

**PATCH /events/{id}/** - **Organisateur UNIQUEMENT** ✋
```python
# IsOrganizerOrReadOnly
return obj.organizer_id == request.user.id  # PAS d'exception pour admins
```
- ✅ L'organisateur propriétaire a accès
- ❌ Les admins (is_staff=True) n'ont PAS accès
- ❌ Les utilisateurs réguliers n'ont PAS accès

**Tous les autres endpoints** - **Organisateur OU Admin** 👥
```python
# IsOrganizerOrAdmin ou GameService._validate_organizer_permission
if event.organizer_id != user.id and not user.is_staff:
    raise PermissionDenied()
```
- ✅ L'organisateur de l'événement a accès
- ✅ Les admins (is_staff=True) ont accès
- ❌ Les utilisateurs réguliers n'ont PAS accès

### Pourquoi cette distinction ?

La modification d'événement (`PATCH`) est considérée comme une **action strictement personnelle** qui ne devrait être effectuée que par le créateur de l'événement.

Les autres actions (suppression, annulation, gestion des jeux) permettent aux admins d'intervenir pour la **gestion et modération** de la plateforme.

## 🔍 Fichiers source de référence

Les permissions sont définies dans :

### Permissions Classes
- `backend/common/permissions.py` : Classe `IsOrganizerOrAdmin`

### Game Service Validation
- `backend/games/services/game_service.py` : Méthodes de validation
  - `_validate_organizer_permission()` (ligne 135)
  - `create_game()` (ligne 232)
  - `reveal_answer()` (ligne 430)
  - `next_question()` (ligne 517)

### Event ViewSet
- `backend/events/views.py` : Configuration des permissions
  - `get_permissions()` (ligne 156)
  - `destroy()` (ligne 214)
  - `cancel()` (ligne 406)
  - `participants()` (ligne 463)

## 🛠️ Dépannage

### Problème : 401 Unauthorized
**Solution** : Vérifiez que les tokens JWT sont valides et non expirés. Réexécutez les requêtes de login.

### Problème : 404 Not Found
**Solution** : Vérifiez que les IDs (`event_id`, `game_id`) dans les variables sont corrects.

### Problème : 400 Bad Request sur Create Game
**Solution** :
- Vérifiez que l'événement existe
- Vérifiez qu'il n'y a pas déjà un jeu actif pour cet événement
- Utilisez `skip_time_validation: true` pour les tests

### Problème : 403 pour l'organisateur
**Solution** :
- Vérifiez que l'utilisateur connecté est bien l'organisateur de l'événement
- Vérifiez que l'`event_id` correspond à un événement créé par cet organisateur

## 📞 Support

Pour toute question ou problème avec la collection, référez-vous à :
- La documentation de l'API : `http://localhost:8000/api/docs/`
- Le code source des permissions : `backend/common/permissions.py`
- Les services de jeu : `backend/games/services/game_service.py`

## 🎯 Conclusion

Cette collection démontre efficacement que les endpoints critiques (création de jeu, gestion des questions, annulation d'événement, etc.) sont correctement protégés et accessibles uniquement par les organisateurs et admins.

Les utilisateurs réguliers reçoivent systématiquement une erreur **403 Forbidden** lorsqu'ils tentent d'accéder à ces endpoints, ce qui prouve que les permissions fonctionnent correctement.
