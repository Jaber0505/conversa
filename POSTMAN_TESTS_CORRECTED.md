# Guide de Test Postman - Conversa API (ROUTES RÉELLES)

## 🎯 URL de Base

```
BASE_URL = http://localhost:8000
API_VERSION = /api/v1
```

## ⚙️ Configuration Postman

### Variables d'Environnement

Créer un environnement "Conversa Dev" :

```json
{
  "base_url": "http://localhost:8000",
  "api_v1": "http://localhost:8000/api/v1",
  "access_token": "",
  "refresh_token": "",
  "user_id": "",
  "event_id": "",
  "booking_public_id": "",
  "game_id": "",
  "partner_id": "1",
  "language_id": "1"
}
```

---

## 🔐 AUTHENTIFICATION

### 1. Inscription

**Endpoint** : `POST {{api_v1}}/auth/register/`

**Headers** :
```
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "email": "jean.dupont@example.com",
  "password": "MonMotDePasse123!",
  "first_name": "Jean",
  "last_name": "Dupont"
}
```

**Résultat attendu** :
- ✅ `201 Created`
- Response :
```json
{
  "id": 1,
  "email": "jean.dupont@example.com",
  "first_name": "Jean",
  "last_name": "Dupont"
}
```

**Script Post-Response (Tests tab)** :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("user_id", response.id);
    console.log("User ID saved:", response.id);
}
```

---

### 2. Connexion

**Endpoint** : `POST {{api_v1}}/auth/login/`

**Headers** :
```
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "email": "jean.dupont@example.com",
  "password": "MonMotDePasse123!"
}
```

**Résultat attendu** :
- ✅ `200 OK`
- Response :
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Script Post-Response** :
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("access_token", response.access);
    pm.environment.set("refresh_token", response.refresh);
    console.log("Tokens saved!");
}
```

---

### 3. Obtenir Mon Profil

**Endpoint** : `GET {{api_v1}}/auth/me/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK`
- Response :
```json
{
  "id": 1,
  "email": "jean.dupont@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "is_staff": false
}
```

---

### 4. Rafraîchir Token

**Endpoint** : `POST {{api_v1}}/auth/refresh/`

**Headers** :
```
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "refresh": "{{refresh_token}}"
}
```

**Résultat attendu** :
- ✅ `200 OK`
- Nouveau `access` token

---

### 5. Déconnexion

**Endpoint** : `POST {{api_v1}}/auth/logout/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "refresh": "{{refresh_token}}"
}
```

**Résultat attendu** :
- ✅ `200 OK`
- Token blacklisté

---

## 📅 ÉVÉNEMENTS

### 6. Créer Événement (DRAFT)

**Endpoint** : `POST {{api_v1}}/events/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "partner": 1,
  "language": 1,
  "theme": "Conversation sur le cinéma français",
  "difficulty": "medium",
  "datetime_start": "2025-01-25T14:00:00Z",
  "game_type": "picture_description"
}
```

**Résultat attendu** :
- ✅ `201 Created`
- Response :
```json
{
  "id": 1,
  "status": "DRAFT",
  "theme": "Conversation sur le cinéma français",
  "difficulty": "medium",
  "organizer_id": 1,
  "partner_name": "Café de la Paix",
  "price_cents": 700
}
```

**Script Post-Response** :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("event_id", response.id);
    console.log("Event ID saved:", response.id);
}
```

---

### 7. Lister Événements

**Endpoint** : `GET {{api_v1}}/events/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Query Params (optionnels)** :
- `partner=1` (filtrer par partner)
- `language=fr` (filtrer par langue)
- `ordering=-datetime_start` (trier)

**Résultat attendu** :
- ✅ `200 OK`
- Liste : événements PUBLISHED + mes DRAFT

---

### 8. Voir Détail Événement

**Endpoint** : `GET {{api_v1}}/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK`
- Détails complets de l'événement

---

### 9. Modifier Événement

**Endpoint** : `PATCH {{api_v1}}/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "theme": "Conversation sur le cinéma italien"
}
```

**Résultat attendu** :
- ✅ `200 OK` (si organisateur)
- ❌ `403 Forbidden` (si non-organisateur)

---

### 10. Publier Événement (Payer et Publier)

**Endpoint** : `POST {{api_v1}}/events/{{event_id}}/pay-and-publish/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "lang": "fr"
}
```

**Résultat attendu** :
- ✅ `200 OK`
- Response :
```json
{
  "url": "https://checkout.stripe.com/..."
}
```

---

### 11. Annuler Événement

**Endpoint** : `POST {{api_v1}}/events/{{event_id}}/cancel/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK` (si >3h avant et organisateur)
- ❌ `403 Forbidden` (si non-organisateur)
- ❌ `400 Bad Request` (si <3h avant)

---

### 12. Supprimer Événement DRAFT

**Endpoint** : `DELETE {{api_v1}}/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `204 No Content` (si DRAFT et organisateur)
- ❌ `409 Conflict` (si PUBLISHED)

---

## 🎫 RÉSERVATIONS

### 13. Créer Réservation

**Endpoint** : `POST {{api_v1}}/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "event": 1
}
```

**Résultat attendu** :
- ✅ `201 Created` (si événement PUBLISHED)
- ❌ `400 Bad Request` (si événement DRAFT)
- Response :
```json
{
  "id": 1,
  "public_id": "abc123def456",
  "event": 1,
  "user": 1,
  "status": "PENDING",
  "amount_cents": 700
}
```

**Script Post-Response** :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("booking_public_id", response.public_id);
    console.log("Booking ID saved:", response.public_id);
}
```

---

### 14. Lister Mes Réservations

**Endpoint** : `GET {{api_v1}}/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK`
- Liste de toutes mes réservations

---

### 15. Voir Détail Réservation

**Endpoint** : `GET {{api_v1}}/bookings/{{booking_public_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK` (si c'est ma réservation)
- ❌ `404 Not Found` (si réservation d'un autre)

---

### 16. Annuler Réservation

**Endpoint** : `POST {{api_v1}}/bookings/{{booking_public_id}}/cancel/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK` (si >3h avant événement)
- ❌ `400 Bad Request` (si <3h avant)

---

## 💳 PAIEMENTS

### 17. Créer Session Stripe (Payer Réservation)

**Endpoint** : `POST {{api_v1}}/payments/checkout/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "booking_public_id": "{{booking_public_id}}",
  "lang": "fr"
}
```

**Résultat attendu** :
- ✅ `200 OK`
- Response :
```json
{
  "url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

---

## 🎮 JEUX

### 18. Créer Jeu

**Endpoint** : `POST {{api_v1}}/games/create/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "event_id": 1,
  "game_type": "picture_description"
}
```

**Résultat attendu** :
- ✅ `201 Created` (si organisateur)
- ❌ `403 Forbidden` (si non-organisateur)
- Response :
```json
{
  "id": 1,
  "event": 1,
  "game_type": "picture_description",
  "status": "ACTIVE",
  "question": {
    "image_url": "...",
    "options": ["A", "B", "C", "D"]
  }
}
```

**Script Post-Response** :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("game_id", response.id);
    console.log("Game ID saved:", response.id);
}
```

---

### 19. Obtenir Jeu Actif

**Endpoint** : `GET {{api_v1}}/games/active/?event_id={{event_id}}`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK` (si organisateur OU participant confirmé)
- ❌ `403 Forbidden` (si sans réservation)
- ❌ `404 Not Found` (si pas de jeu actif)

---

### 20. Lister Jeux

**Endpoint** : `GET {{api_v1}}/games/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Query Params (optionnels)** :
- `event_id=1`
- `status=ACTIVE`

**Résultat attendu** :
- ✅ `200 OK`
- Liste des jeux accessibles

---

### 21. Voir Détail Jeu

**Endpoint** : `GET {{api_v1}}/games/{{game_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK` (si participant ou organisateur)
- ❌ `403 Forbidden` (si sans accès)

---

### 22. Voter

**Endpoint** : `POST {{api_v1}}/games/{{game_id}}/vote/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "answer": "A"
}
```

**Résultat attendu** :
- ✅ `201 Created` (premier vote)
- ❌ `400 Bad Request` (si déjà voté)

---

### 23. Révéler Réponse

**Endpoint** : `POST {{api_v1}}/games/{{game_id}}/reveal/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK` (si organisateur)
- ❌ `403 Forbidden` (si non-organisateur)

---

### 24. Obtenir Statistiques Jeu

**Endpoint** : `GET {{api_v1}}/games/{{game_id}}/stats/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK`
- Response :
```json
{
  "total_votes": 5,
  "vote_distribution": {
    "A": 3,
    "B": 2
  },
  "has_majority": true
}
```

---

## 🏢 PARTNERS

### 25. Lister Partners

**Endpoint** : `GET {{api_v1}}/partners/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Query Params (optionnels)** :
- `postal_code=1000`

**Résultat attendu** :
- ✅ `200 OK`
- Liste des partners

---

### 26. Voir Détail Partner

**Endpoint** : `GET {{api_v1}}/partners/{{partner_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK`
- Détails du partner

---

## 🌍 LANGUES

### 27. Lister Langues

**Endpoint** : `GET {{api_v1}}/languages/`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK`
- Liste des langues disponibles

---

## 🔒 TESTS DE SÉCURITÉ

### 28. Accès Sans Token

**Endpoint** : `GET {{api_v1}}/auth/me/`

**Headers** :
```
(Aucun header Authorization)
```

**Résultat attendu** :
- ❌ `401 Unauthorized`
- Message : `"detail": "Authentication credentials were not provided."`

---

### 29. Token Invalide

**Endpoint** : `GET {{api_v1}}/auth/me/`

**Headers** :
```
Authorization: Bearer invalid_token_here
```

**Résultat attendu** :
- ❌ `401 Unauthorized`
- Message : `"detail": "Given token not valid for any token type"`

---

### 30. SQL Injection dans Filter

**Endpoint** : `GET {{api_v1}}/events/?partner=1' OR '1'='1`

**Headers** :
```
Authorization: Bearer {{access_token}}
```

**Résultat attendu** :
- ✅ `200 OK`
- Liste vide (injection bloquée par ORM)

---

### 31. SQL Injection dans POST

**Endpoint** : `POST {{api_v1}}/bookings/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "event": "1; DROP TABLE bookings;--"
}
```

**Résultat attendu** :
- ❌ `400 Bad Request`
- Message : `"event": ["A valid integer is required."]`

---

### 32. XSS dans Theme

**Endpoint** : `POST {{api_v1}}/events/`

**Headers** :
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "partner": 1,
  "language": 1,
  "theme": "<script>alert('XSS')</script>",
  "difficulty": "easy",
  "datetime_start": "2025-01-25T14:00:00Z",
  "game_type": "debate"
}
```

**Résultat attendu** :
- ✅ `201 Created`
- Theme stocké tel quel (échappé dans le frontend)

---

### 33. Accès DRAFT Non Autorisé

**Prérequis** : Créer 2 utilisateurs avec tokens différents

**Endpoint** : `GET {{api_v1}}/events/{{draft_event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token_user2}}
```

**Résultat attendu** :
- ❌ `404 Not Found`
- User2 ne peut pas voir le DRAFT de User1

---

### 34. Modifier Événement Non Autorisé

**Endpoint** : `PATCH {{api_v1}}/events/{{event_id}}/`

**Headers** :
```
Authorization: Bearer {{access_token_user2}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "theme": "HACK ATTEMPT"
}
```

**Résultat attendu** :
- ❌ `403 Forbidden`

---

### 35. Créer Jeu Sans Être Organisateur

**Endpoint** : `POST {{api_v1}}/games/create/`

**Headers** :
```
Authorization: Bearer {{access_token_user2}}
Content-Type: application/json
```

**Body (JSON)** :
```json
{
  "event_id": 1,
  "game_type": "picture_description"
}
```

**Résultat attendu** :
- ❌ `403 Forbidden`

---

### 36. Rejoindre Jeu Sans Réservation

**Endpoint** : `GET {{api_v1}}/games/active/?event_id={{event_id}}`

**Headers** :
```
Authorization: Bearer {{access_token_user3}}
```

**Résultat attendu** :
- ❌ `403 Forbidden`

---

## 📊 WORKFLOW COMPLET

### Scénario : Créer et Publier un Événement

```
1. POST /api/v1/auth/register/
   → Créer compte

2. POST /api/v1/auth/login/
   → Obtenir tokens

3. POST /api/v1/events/
   → Créer événement DRAFT

4. POST /api/v1/events/{id}/pay-and-publish/
   → Obtenir URL Stripe

5. [Payer sur Stripe - simulation]
   → Événement passe en PUBLISHED

6. [Autre utilisateur] POST /api/v1/bookings/
   → Créer réservation

7. [Autre utilisateur] POST /api/v1/payments/checkout/
   → Payer réservation

8. [Organisateur] POST /api/v1/games/create/
   → Lancer le jeu

9. [Participants] POST /api/v1/games/{id}/vote/
   → Voter

10. [Organisateur] POST /api/v1/games/{id}/reveal/
    → Révéler réponse
```

---

## ✅ CHECKLIST DE TEST

### Authentification
- [ ] Inscription réussie
- [ ] Connexion réussie (tokens sauvegardés)
- [ ] Obtenir profil avec token
- [ ] Refus sans token (401)
- [ ] Refus avec token invalide (401)

### Événements - Organisateur
- [ ] Créer DRAFT (201)
- [ ] Voir mon DRAFT (200)
- [ ] Modifier mon événement (200)
- [ ] Supprimer mon DRAFT (204)
- [ ] Publier mon événement (200 avec URL)

### Événements - Non-organisateur
- [ ] Ne peut pas voir DRAFT autre (404)
- [ ] Ne peut pas modifier événement autre (403)
- [ ] Peut voir événements PUBLISHED (200)

### Réservations
- [ ] Créer sur PUBLISHED (201)
- [ ] Impossible sur DRAFT (400)
- [ ] Voir mes réservations (200)
- [ ] Ne peut pas voir réservations autre (404)
- [ ] Annuler ma réservation >3h (200)
- [ ] Impossible annuler <3h (400)

### Jeux
- [ ] Créer jeu organisateur (201)
- [ ] Impossible créer non-org (403)
- [ ] Rejoindre avec réservation (200)
- [ ] Impossible sans réservation (403)
- [ ] Voter (201)
- [ ] Impossible voter 2x (400)

### Sécurité
- [ ] SQL injection bloquée
- [ ] XSS échappé
- [ ] Tokens validés
- [ ] Permissions respectées

---

## 🚀 IMPORT DANS POSTMAN

1. Créer Collection "Conversa API v1"
2. Créer Environnement "Conversa Dev"
3. Définir variables (base_url, api_v1, tokens)
4. Commencer par Register puis Login
5. Tester dans l'ordre du workflow

---

**Version** : 1.0 (Corrigée avec routes réelles)
**Date** : 2025-01-13
