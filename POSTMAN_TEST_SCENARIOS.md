# Guide de Test Postman - Conversa API

## 📋 Table des Matières

1. [Configuration Initiale](#configuration-initiale)
2. [Scénarios d'Authentification](#scénarios-dauthentification)
3. [Scénarios Événements](#scénarios-événements)
4. [Scénarios Réservations](#scénarios-réservations)
5. [Scénarios Jeux](#scénarios-jeux)
6. [Tests de Sécurité](#tests-de-sécurité)

---

## Configuration Initiale

### Variables d'Environnement Postman

Créer un environnement "Conversa Dev" avec ces variables :

```json
{
  "base_url": "http://localhost:8000",
  "access_token": "",
  "refresh_token": "",
  "user_id": "",
  "event_id": "",
  "booking_id": "",
  "game_id": ""
}
```

---

## Scénarios d'Authentification

### 🔓 Scénario 1.1 : Inscription (Non authentifié)

**Endpoint** : `POST {{base_url}}/api/users/register/`

**Headers** :
```
Content-Type: application/json
```

**Body** :
```json
{
  "email": "testuser@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Résultat attendu** :
- ✅ Status: `201 Created`
- Response contient : `id`, `email`, `first_name`, `last_name`

**Script Post-Response** (pour sauvegarder l'ID) :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("user_id", response.id);
}
```

---

### 🔓 Scénario 1.2 : Connexion (Non authentifié)

**Endpoint** : `POST {{base_url}}/api/users/login/`

**Headers** :
```
Content-Type: application/json
```

**Body** :
```json
{
  "email": "testuser@example.com",
  "password": "SecurePass123!"
}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Response contient : `access`, `refresh`

**Script Post-Response** :
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("access_token", response.access);
    pm.environment.set("refresh_token", response.refresh);
}
```

---

### 🔒 Scénario 1.3 : Obtenir Profil (Authentifié)

**Endpoint** : `GET {{base_url}}/api/users/me/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Response contient : `id`, `email`, `first_name`, `last_name`, `is_staff`

---

### 🔓 Scénario 1.4 : Connexion Échouée (Mauvais mot de passe)

**Endpoint** : `POST {{base_url}}/api/users/login/`

**Body** :
```json
{
  "email": "testuser@example.com",
  "password": "WrongPassword"
}
```

**Résultat attendu** :
- ❌ Status: `401 Unauthorized`
- Message d'erreur

---

### 🔓 Scénario 1.5 : Accès sans Token (Non authentifié)

**Endpoint** : `GET {{base_url}}/api/users/me/`

**Headers** :
```
(Aucun header Authorization)
```

**Résultat attendu** :
- ❌ Status: `401 Unauthorized`
- Message: `"Authentication credentials were not provided."`

---

## Scénarios Événements

### 🔒 Scénario 2.1 : Créer Événement en DRAFT (Organisateur)

**Endpoint** : `POST {{base_url}}/api/events/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "partner": 1,
  "language": 1,
  "theme": "Conversation sur le cinéma français",
  "difficulty": "medium",
  "datetime_start": "2025-01-20T14:00:00Z",
  "game_type": "picture_description"
}
```

**Résultat attendu** :
- ✅ Status: `201 Created`
- Response : `status: "DRAFT"`, `organizer_id: <your_user_id>`

**Script Post-Response** :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("event_id", response.id);
}
```

---

### 🔒 Scénario 2.2 : Lister Événements (Authentifié)

**Endpoint** : `GET {{base_url}}/api/events/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Liste contient : événements PUBLISHED + mes propres DRAFT

---

### 🔒 Scénario 2.3 : Voir Détail Événement DRAFT (Organisateur)

**Endpoint** : `GET {{base_url}}/api/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Response contient les détails complets

---

### 🔒 Scénario 2.4 : Voir DRAFT d'un Autre (Non organisateur)

**Prérequis** : Créer un deuxième utilisateur et obtenir son token

**Endpoint** : `GET {{base_url}}/api/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token_user2}}
```

**Résultat attendu** :
- ❌ Status: `404 Not Found`
- L'utilisateur 2 ne voit pas le DRAFT de l'utilisateur 1

---

### 🔒 Scénario 2.5 : Publier Événement (Organisateur)

**Endpoint** : `POST {{base_url}}/api/events/{{event_id}}/pay-and-publish/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "lang": "fr"
}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Response contient : `url` (Stripe checkout session)

---

### 🔒 Scénario 2.6 : Modifier Événement (Organisateur)

**Endpoint** : `PATCH {{base_url}}/api/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "theme": "Conversation sur le cinéma italien"
}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- `theme` est mis à jour

---

### 🔒 Scénario 2.7 : Modifier Événement d'un Autre (Non organisateur)

**Endpoint** : `PATCH {{base_url}}/api/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token_user2}}
Content-Type: application/json
```

**Body** :
```json
{
  "theme": "HACK ATTEMPT"
}
```

**Résultat attendu** :
- ❌ Status: `403 Forbidden`
- Message: Permission denied

---

### 🔒 Scénario 2.8 : Supprimer Événement DRAFT (Organisateur)

**Endpoint** : `DELETE {{base_url}}/api/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `204 No Content`
- Événement supprimé

---

### 🔒 Scénario 2.9 : Supprimer Événement PUBLISHED (Tentative)

**Endpoint** : `DELETE {{base_url}}/api/events/{{published_event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ❌ Status: `409 Conflict`
- Message: "Cannot hard delete a non-draft event. Use the cancel endpoint."

---

### 🔒 Scénario 2.10 : Annuler Événement (Organisateur)

**Endpoint** : `POST {{base_url}}/api/events/{{event_id}}/cancel/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- `status: "CANCELLED"`

---

### 🔒 Scénario 2.11 : Filtrer par Partner

**Endpoint** : `GET {{base_url}}/api/events/?partner=1`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Liste contient uniquement les événements du partner 1

---

### 🔒 Scénario 2.12 : Filtrer par Langue

**Endpoint** : `GET {{base_url}}/api/events/?language=fr`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Liste contient uniquement les événements en français

---

### 🔒 Scénario 2.13 : Trier par Date

**Endpoint** : `GET {{base_url}}/api/events/?ordering=-datetime_start`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Événements triés du plus récent au plus ancien

---

## Scénarios Réservations

### 🔒 Scénario 3.1 : Créer Réservation sur Événement PUBLISHED

**Prérequis** : Avoir un événement PUBLISHED

**Endpoint** : `POST {{base_url}}/api/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "event": {{published_event_id}}
}
```

**Résultat attendu** :
- ✅ Status: `201 Created`
- Response : `status: "PENDING"`, `public_id`, `amount_cents`

**Script Post-Response** :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("booking_id", response.public_id);
}
```

---

### 🔒 Scénario 3.2 : Créer Réservation sur Événement DRAFT

**Endpoint** : `POST {{base_url}}/api/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "event": {{draft_event_id}}
}
```

**Résultat attendu** :
- ❌ Status: `400 Bad Request`
- Message: "Event is not available for booking."

---

### 🔒 Scénario 3.3 : Lister Mes Réservations

**Endpoint** : `GET {{base_url}}/api/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Liste de toutes mes réservations (PENDING, CONFIRMED, CANCELLED)

---

### 🔒 Scénario 3.4 : Voir Détail d'une Réservation

**Endpoint** : `GET {{base_url}}/api/bookings/{{booking_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Détails complets de la réservation

---

### 🔒 Scénario 3.5 : Voir Réservation d'un Autre

**Endpoint** : `GET {{base_url}}/api/bookings/{{booking_id_user2}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ❌ Status: `404 Not Found`
- On ne peut voir que ses propres réservations

---

### 🔒 Scénario 3.6 : Annuler Réservation CONFIRMED

**Endpoint** : `POST {{base_url}}/api/bookings/{{booking_id}}/cancel/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- `status: "CANCELLED"`

---

### 🔒 Scénario 3.7 : Payer Réservation (Créer Session Stripe)

**Endpoint** : `POST {{base_url}}/api/payments/checkout/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "booking_public_id": "{{booking_id}}",
  "lang": "fr"
}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Response contient : `url` (Stripe checkout session)

---

### 🔒 Scénario 3.8 : Créer Doublon Réservation PENDING

**Endpoint** : `POST {{base_url}}/api/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "event": {{published_event_id}}
}
```

**Résultat attendu** :
- ❌ Status: `400 Bad Request`
- Message: "You already have a pending booking for this event."

---

### 🔒 Scénario 3.9 : Annuler Réservation 2h Avant Événement

**Prérequis** : Événement commence dans moins de 3h

**Endpoint** : `POST {{base_url}}/api/bookings/{{booking_id}}/cancel/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ❌ Status: `400 Bad Request`
- Message: "Cannot cancel within 3 hours of event start."

---

## Scénarios Jeux

### 🔒 Scénario 4.1 : Créer Jeu (Organisateur)

**Prérequis** : Avoir un événement PUBLISHED dont tu es l'organisateur

**Endpoint** : `POST {{base_url}}/api/games/create/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "event_id": {{published_event_id}},
  "game_type": "picture_description"
}
```

**Résultat attendu** :
- ✅ Status: `201 Created`
- Response : `id`, `event`, `game_type`, `status: "ACTIVE"`, `question`

**Script Post-Response** :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("game_id", response.id);
}
```

---

### 🔒 Scénario 4.2 : Créer Jeu (Non organisateur)

**Endpoint** : `POST {{base_url}}/api/games/create/`

**Headers** :
```
Authorization: Bearer {{access_token_user2}}
Content-Type: application/json
```

**Body** :
```json
{
  "event_id": {{published_event_id}},
  "game_type": "picture_description"
}
```

**Résultat attendu** :
- ❌ Status: `403 Forbidden`
- Message: "Only event organizer can create games."

---

### 🔒 Scénario 4.3 : Obtenir Jeu Actif (Participant Confirmé)

**Endpoint** : `GET {{base_url}}/api/games/active/?event_id={{published_event_id}}`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Détails du jeu actif

---

### 🔒 Scénario 4.4 : Obtenir Jeu Actif (Sans Réservation)

**Endpoint** : `GET {{base_url}}/api/games/active/?event_id={{published_event_id}}`

**Headers** :
```
Authorization: Bearer {{access_token_user3}}
```

**Résultat attendu** :
- ❌ Status: `403 Forbidden`
- Message: "You do not have access to this event"

---

### 🔒 Scénario 4.5 : Voter (Participant)

**Endpoint** : `POST {{base_url}}/api/games/{{game_id}}/vote/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "answer": "Option A"
}
```

**Résultat attendu** :
- ✅ Status: `201 Created`
- Response : jeu mis à jour avec le vote

---

### 🔒 Scénario 4.6 : Voter Deux Fois (Tentative)

**Endpoint** : `POST {{base_url}}/api/games/{{game_id}}/vote/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "answer": "Option B"
}
```

**Résultat attendu** :
- ❌ Status: `400 Bad Request`
- Message: "You have already voted in this game."

---

### 🔒 Scénario 4.7 : Révéler Réponse (Organisateur)

**Endpoint** : `POST {{base_url}}/api/games/{{game_id}}/reveal/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Response : jeu avec `correct_answer` visible

---

### 🔒 Scénario 4.8 : Révéler Réponse (Non organisateur)

**Endpoint** : `POST {{base_url}}/api/games/{{game_id}}/reveal/`

**Headers** :
```
Authorization: Bearer {{access_token_user2}}
```

**Résultat attendu** :
- ❌ Status: `403 Forbidden`
- Message: "Only organizer can reveal answers."

---

### 🔒 Scénario 4.9 : Lister Mes Jeux

**Endpoint** : `GET {{base_url}}/api/games/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Liste des jeux des événements où je participe ou organise

---

### 🔒 Scénario 4.10 : Obtenir Statistiques Jeu

**Endpoint** : `GET {{base_url}}/api/games/{{game_id}}/stats/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Response : `total_votes`, `vote_distribution`, `has_majority`

---

## Tests de Sécurité

### 🔐 Scénario 5.1 : SQL Injection dans Filter

**Endpoint** : `GET {{base_url}}/api/events/?partner=1' OR '1'='1`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ Status: `200 OK`
- Liste vide ou erreur de validation (pas d'injection)

---

### 🔐 Scénario 5.2 : SQL Injection dans POST

**Endpoint** : `POST {{base_url}}/api/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "event": "1; DROP TABLE bookings;--"
}
```

**Résultat attendu** :
- ❌ Status: `400 Bad Request`
- Message: "A valid integer is required."

---

### 🔐 Scénario 5.3 : XSS dans Theme

**Endpoint** : `POST {{base_url}}/api/events/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body** :
```json
{
  "partner": 1,
  "language": 1,
  "theme": "<script>alert('XSS')</script>",
  "difficulty": "medium",
  "datetime_start": "2025-01-20T14:00:00Z",
  "game_type": "picture_description"
}
```

**Résultat attendu** :
- ✅ Status: `201 Created`
- Theme est échappé dans le HTML frontend

---

### 🔐 Scénario 5.4 : Token Expiré

**Endpoint** : `GET {{base_url}}/api/users/me/`

**Headers** :
```
Authorization: Bearer expired_token_here
```

**Résultat attendu** :
- ❌ Status: `401 Unauthorized`
- Message: "Token is invalid or expired"

---

### 🔐 Scénario 5.5 : Token Malformé

**Endpoint** : `GET {{base_url}}/api/users/me/`

**Headers** :
```
Authorization: Bearer not.a.valid.jwt
```

**Résultat attendu** :
- ❌ Status: `401 Unauthorized`
- Message: "Invalid token"

---

### 🔐 Scénario 5.6 : CSRF Attack Simulation

**Note** : Django REST Framework avec JWT n'utilise pas CSRF pour les requêtes API

**Endpoint** : `POST {{base_url}}/api/events/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
(Pas de CSRF Token)
```

**Body** :
```json
{
  "partner": 1,
  "language": 1,
  "theme": "Test",
  "difficulty": "easy",
  "datetime_start": "2025-01-20T14:00:00Z",
  "game_type": "debate"
}
```

**Résultat attendu** :
- ✅ Status: `201 Created`
- JWT suffit, pas besoin de CSRF token pour API

---

### 🔐 Scénario 5.7 : Rate Limiting

**Endpoint** : `POST {{base_url}}/api/users/login/`

**Répéter 50 fois rapidement**

**Body** :
```json
{
  "email": "test@example.com",
  "password": "wrong"
}
```

**Résultat attendu** :
- Après N tentatives : ❌ Status: `429 Too Many Requests`
- Message: "Request was throttled."

---

### 🔐 Scénario 5.8 : Access avec Staff Permission (Non-staff)

**Endpoint** : `GET {{base_url}}/api/admin/audit-logs/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ❌ Status: `403 Forbidden`
- Message: "You do not have permission to perform this action."

---

### 🔐 Scénario 5.9 : Énumération d'Utilisateurs

**Endpoint** : `POST {{base_url}}/api/users/register/`

**Body** :
```json
{
  "email": "existing@example.com",
  "password": "Test123!",
  "first_name": "Test",
  "last_name": "User"
}
```

**Résultat attendu** :
- ❌ Status: `400 Bad Request`
- Message générique (ne révèle pas si l'email existe)

---

### 🔐 Scénario 5.10 : Path Traversal

**Endpoint** : `GET {{base_url}}/api/events/../../../etc/passwd`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ❌ Status: `404 Not Found`
- Django router bloque le path traversal

---

## 📊 Collection Postman Complète

### Structure Recommandée

```
📁 Conversa API Tests
├── 📁 1. Authentication
│   ├── Register
│   ├── Login (Save Token)
│   ├── Get Me
│   ├── Refresh Token
│   └── Logout
├── 📁 2. Events - CRUD
│   ├── Create Event (DRAFT)
│   ├── List Events
│   ├── Get Event Details
│   ├── Update Event
│   ├── Delete Event
│   └── Cancel Event
├── 📁 3. Events - Permissions
│   ├── View Own DRAFT (Organizer)
│   ├── View Other's DRAFT (Non-org) ❌
│   ├── Modify Own Event (Organizer)
│   └── Modify Other's Event (Non-org) ❌
├── 📁 4. Bookings
│   ├── Create Booking (PUBLISHED)
│   ├── Create Booking (DRAFT) ❌
│   ├── List My Bookings
│   ├── Cancel Booking
│   └── Pay Booking
├── 📁 5. Games
│   ├── Create Game (Organizer)
│   ├── Create Game (Non-org) ❌
│   ├── Get Active Game
│   ├── Vote
│   └── Reveal Answer
└── 📁 6. Security Tests
    ├── SQL Injection Tests
    ├── XSS Tests
    ├── Token Tests
    └── Rate Limiting
```

---

## 🎯 Quick Test Script

Pour tester rapidement tous les endpoints critiques :

### Script 1 : Workflow Complet Utilisateur

```bash
# 1. S'inscrire
POST /api/users/register/

# 2. Se connecter (sauvegarder token)
POST /api/users/login/

# 3. Créer événement
POST /api/events/

# 4. Publier événement
POST /api/events/{id}/pay-and-publish/

# 5. Créer réservation (avec autre user)
POST /api/bookings/

# 6. Lancer jeu
POST /api/games/create/

# 7. Voter
POST /api/games/{id}/vote/

# 8. Révéler réponse
POST /api/games/{id}/reveal/
```

### Script 2 : Tests de Sécurité

```bash
# Test 1: Accès sans token
GET /api/users/me/ (sans Authorization)

# Test 2: SQL Injection
GET /api/events/?partner=1' OR '1'='1

# Test 3: Accès DRAFT non autorisé
GET /api/events/{draft_id}/ (avec token autre user)

# Test 4: Modification non autorisée
PATCH /api/events/{id}/ (avec token autre user)

# Test 5: Créer jeu sans être organisateur
POST /api/games/create/ (avec token autre user)
```

---

## 📝 Checklist de Test

### Authentification
- [ ] Inscription réussie
- [ ] Connexion réussie
- [ ] Obtenir profil avec token valide
- [ ] Refus d'accès sans token
- [ ] Refus avec token expiré

### Événements - Organisateur
- [ ] Créer événement DRAFT
- [ ] Voir mes DRAFT
- [ ] Modifier mon événement
- [ ] Supprimer mon DRAFT
- [ ] Publier mon événement

### Événements - Non-organisateur
- [ ] ❌ Ne peut pas voir DRAFT des autres
- [ ] ❌ Ne peut pas modifier événements des autres
- [ ] ❌ Ne peut pas supprimer événements des autres
- [ ] ✅ Peut voir événements PUBLISHED

### Réservations
- [ ] Créer réservation sur PUBLISHED
- [ ] ❌ Ne peut pas réserver sur DRAFT
- [ ] Voir mes réservations
- [ ] ❌ Ne peut pas voir réservations des autres
- [ ] Annuler ma réservation (>3h avant)
- [ ] ❌ Ne peut pas annuler (<3h avant)

### Jeux
- [ ] Créer jeu (organisateur)
- [ ] ❌ Ne peut pas créer jeu (non-org)
- [ ] Rejoindre jeu actif (participant)
- [ ] ❌ Ne peut pas rejoindre (sans réservation)
- [ ] Voter
- [ ] ❌ Ne peut pas voter deux fois
- [ ] Révéler réponse (organisateur)
- [ ] ❌ Ne peut pas révéler (non-org)

### Sécurité
- [ ] SQL Injection bloquée
- [ ] XSS échappé
- [ ] Token invalide rejeté
- [ ] Rate limiting actif
- [ ] Path traversal bloqué

---

## 🚀 Import dans Postman

1. Copier ce markdown
2. Dans Postman : `Import` → `Raw text`
3. Postman détecte automatiquement les requêtes
4. Configurer l'environnement avec `base_url`
5. Commencer par "Register" puis "Login" pour obtenir le token

---

**Document créé le** : 2025-01-13
**Dernière mise à jour** : 2025-01-13
**Version** : 1.0
