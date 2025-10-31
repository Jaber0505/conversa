# 🔒 Audit de Sécurité & API - Frontend Conversa

**Date**: 20 octobre 2025
**Score Global Sécurité**: **8.5/10** ✅
**Score Global Fonctionnel**: **9/10** ✅

---

## 📋 Table des Matières

1. [Sécurité](#-sécurité)
2. [Toutes les URLs/Routes](#-toutes-les-urlsroutes)
3. [Appels API](#-appels-api)
4. [Bugs Potentiels](#-bugs-potentiels)
5. [Recommandations](#-recommandations)

---

## 🔒 Sécurité

### ✅ Points Forts

#### 1. **Protection XSS** (10/10) ✅
```typescript
// t-html.directive.ts (ligne 45)
const safe = this.sanitizer.sanitize(SecurityContext.HTML, raw) ?? '';
this.r.setProperty(this.el.nativeElement, 'innerHTML', safe);
```
- ✅ **Utilise DomSanitizer d'Angular**
- ✅ **Sanitize avec SecurityContext.HTML**
- ✅ **Aucun innerHTML brut détecté**
- ✅ **Aucun `eval()` ou `new Function()` trouvé**

#### 2. **Authentification JWT** (9/10) ✅
```typescript
// auth.interceptor.ts
- ✅ Refresh token automatique sur 401
- ✅ Gate anti-double-refresh (refreshInFlight$)
- ✅ Tokens stockés dans localStorage (pas de cookies)
- ✅ Vérification d'expiration JWT (jwtExp)
- ✅ Synchronisation multi-onglets (storage event)
```

**Détails**:
- **Access Token**: Ajouté automatiquement dans `Authorization: Bearer {token}`
- **Refresh Token**: Refresh auto avant expiration
- **Logout**: Clear tokens + redirect

**Endpoints protégés**:
```typescript
// Exclusions (pas de token attaché):
- /auth/login/
- /auth/register/
- /auth/refresh/
```

#### 3. **Guards de Route** (8/10) ✅
```typescript
// authGuard: Protège les routes authentifiées
- ✅ Redirige vers /login si pas connecté
- ✅ Conserve l'URL de redirection (?redirect=)

// guestGuard: Empêche accès login/register si connecté
- ✅ Redirige vers home si déjà connecté
```

**⚠️ PROBLÈME**: Route `/bookings` **NON PROTÉGÉE**
```typescript
// app.routes.ts ligne 54
{
  path: 'bookings',
  loadComponent: () => import('...').then(m => m.MyBookingsComponent)
  // ❌ Manque: canActivate: [authGuard]
}
```

#### 4. **Stockage Sécurisé** (7/10) ⚠️
```typescript
// auth-token.service.ts
- ✅ Try-catch autour de localStorage (gère SSR)
- ✅ Pas de données sensibles en clair (seulement JWT)
- ⚠️ localStorage = vulnérable XSS (mais Angular protège bien)
```

**Alternative recommandée**: HttpOnly Cookies (backend)

#### 5. **Protection CSRF** (9/10) ✅
- ✅ JWT dans headers (pas de cookies auto-send)
- ✅ Pas de GET pour mutations
- ✅ POST/PUT/DELETE pour actions importantes

---

### ⚠️ Vulnérabilités Potentielles

#### 1. **Route Bookings Non Protégée** 🔴 **Critique**
**Risque**: Utilisateur non connecté peut accéder à `/fr/bookings`

**Reproduction**:
1. Logout
2. Aller à `http://localhost:4200/fr/bookings`
3. ❌ Accès possible (mais API refuse avec 401)

**Fix**:
```typescript
// app.routes.ts
{
  path: 'bookings',
  canActivate: [authGuard], // ← AJOUTER
  loadComponent: () => import('./features/bookings/my-bookings/my-bookings.component')
    .then(m => m.MyBookingsComponent)
}
```

#### 2. **Pas de Rate Limiting Frontend** 🟡 **Mineur**
- Aucune limite sur login/register
- ⚠️ Possibilité de brute-force (mais backend devrait gérer)

**Recommandation**: Ajouter debounce/throttle sur boutons submit

#### 3. **Console.log en Production** 🟡 **Mineur**
```typescript
// Détectés dans:
- features/events/list/events-list.component.ts:68
- features/bookings/my-bookings/my-bookings.component.ts:71,77,113,119
- features/auth/register/register.component.ts:99
- features/payments/cancel/cancel.component.ts:47
```

**Fix**: Ajouter un service de logging qui désactive en prod

#### 4. **Pas de Content Security Policy** 🟡 **Mineur**
- Aucun CSP header détecté
- ⚠️ Recommandé pour production

---

## 🌐 Toutes les URLs/Routes

### Routes Publiques (accessibles sans login)

| URL | Composant | Guard | Lazy | Description |
|-----|-----------|-------|------|-------------|
| `/` | - | - | - | Redirige vers `/fr` |
| `/:lang` | HomeComponent | languageUrlGuard | ❌ | Page d'accueil |
| `/:lang/login` | AuthLoginComponent | guestGuard | ✅ | Page de connexion |
| `/:lang/register` | AuthRegisterComponent | guestGuard | ✅ | Page d'inscription |
| `/:lang/auth` | - | guestGuard | - | Redirige vers login |
| `/:lang/auth/login` | AuthLoginComponent | guestGuard | ✅ | Page de connexion (alt) |
| `/:lang/auth/register` | AuthRegisterComponent | guestGuard | ✅ | Page d'inscription (alt) |
| `/:lang/events` | EventsListComponent | - | ✅ | Liste des événements |
| `/:lang/faq` | FaqComponent | - | ❌ | FAQ |
| `/:lang/about` | About | - | ❌ | À propos |

### Routes Paiement

| URL | Composant | Guard | Lazy | Description |
|-----|-----------|-------|------|-------------|
| `/:lang/stripe/success` | PaymentSuccessComponent | - | ✅ | Succès paiement Stripe |
| `/:lang/stripe/cancel` | PaymentCancelComponent | - | ✅ | Annulation paiement Stripe |

**Query params attendus**:
- `success`: `?session_id={cs_...}&b={booking_public_id}`
- `cancel`: `?cs={cs_...}&b={booking_public_id}`

### Routes Protégées (login requis)

| URL | Composant | Guard | Lazy | Description |
|-----|-----------|-------|------|-------------|
| `/:lang/bookings` | MyBookingsComponent | ❌ **MANQUANT** | ✅ | Mes réservations |

### Routes de Développement

| URL | Composant | Guard | Lazy | Description |
|-----|-----------|-------|------|-------------|
| `/:lang/mock/mockshared` | MockSharedDemo | - | ✅ | Démo composants (hidden) |

### Langues Supportées

```typescript
// core/i18n/config/languages.config.ts
Langues: fr, en, nl, es
Défaut: fr
```

**Exemples d'URLs complètes**:
```
http://localhost:4200/fr
http://localhost:4200/en/events
http://localhost:4200/nl/login
http://localhost:4200/es/register
http://localhost:4200/fr/bookings
http://localhost:4200/fr/stripe/success?session_id=cs_test_123&b=uuid-abc
```

---

## 🔌 Appels API

### Configuration

```typescript
// environment.ts
Base URL (dev): http://localhost:8000/api/v1
Base URL (prod): [À CONFIGURER]
```

### Endpoints Disponibles

#### 1. **Authentification** (`/auth`)

| Méthode | Endpoint | Auth | Body | Réponse | Description |
|---------|----------|------|------|---------|-------------|
| POST | `/auth/register/` | ❌ | RegisterData | void | Créer un compte |
| POST | `/auth/login/` | ❌ | LoginReq | LoginRes | Se connecter |
| POST | `/auth/refresh/` | ❌ | { refresh } | RefreshRes | Rafraîchir token |
| GET | `/auth/me/` | ✅ | - | MeRes | Profil utilisateur |
| POST | `/auth/logout/` | ✅ | { refresh } | void | Se déconnecter |

**RegisterData**:
```typescript
{
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  age: number;
  bio: string;
  native_langs: string[];  // ex: ["fr", "en"]
  target_langs: string[];  // ex: ["es", "nl"]
  consent_given: boolean;
}
```

**LoginReq/Res**:
```typescript
Request: { email: string; password: string }
Response: { access: string; refresh: string }
```

**MeRes**:
```typescript
{
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  age?: number;
  bio?: string;
  native_langs?: string[];
  target_langs?: string[];
  avatar?: string;
}
```

#### 2. **Événements** (`/events`)

| Méthode | Endpoint | Auth | Query Params | Réponse | Description |
|---------|----------|------|--------------|---------|-------------|
| GET | `/events/` | ❌ | EventsListParams | Paginated<EventDto> | Liste événements |
| GET | `/events/{id}/` | ❌ | - | EventDto | Détail événement |
| POST | `/events/` | ✅ | EventWrite | EventDto | Créer événement |
| PUT | `/events/{id}/` | ✅ | EventWrite | EventDto | Modifier événement |
| PATCH | `/events/{id}/` | ✅ | EventUpdate | EventDto | Modifier partiellement |
| DELETE | `/events/{id}/` | ✅ | - | void | Supprimer événement |

**EventsListParams**:
```typescript
{
  partner?: number;    // Filter par partenaire
  language?: string;   // Filter par langue
  ordering?: string;   // Tri: "datetime_start" ou "-datetime_start"
}
```

**EventDto**:
```typescript
{
  id: number;
  title: string;
  theme: string;
  language_code: string;
  address: string;
  datetime_start: string; // ISO 8601
  price_cents: number;
  is_cancelled: boolean;
  alreadyBooked?: boolean; // Ajouté côté client
}
```

#### 3. **Réservations** (`/bookings`)

| Méthode | Endpoint | Auth | Body | Réponse | Description |
|---------|----------|------|------|---------|-------------|
| GET | `/bookings/` | ✅ | - | Paginated<Booking> | Mes réservations |
| GET | `/bookings/{id}/` | ✅ | - | Booking | Détail réservation |
| POST | `/bookings/` | ✅ | { event: number } | Booking | Créer réservation |
| POST | `/bookings/{public_id}/cancel/` | ✅ | {} | Booking | Annuler réservation |

**Booking**:
```typescript
{
  id: number;
  public_id: string;      // UUID
  event: number;          // Event ID
  status: "PENDING" | "CONFIRMED" | "CANCELLED";
  amount_cents: number;
  created_at: string;
  confirmed_at?: string;
}
```

**TTL**: PENDING bookings expirent après 15 minutes (backend)

#### 4. **Paiements** (`/payments`)

| Méthode | Endpoint | Auth | Body | Réponse | Description |
|---------|----------|------|------|---------|-------------|
| POST | `/payments/checkout-session/` | ✅ | CheckoutPayload | CheckoutSessionCreated | Créer session Stripe |

**CheckoutPayload**:
```typescript
{
  booking_public_id: string;
  lang: string;              // "fr", "en", "nl", "es"
  success_url?: string;      // Optionnel (défaut: /stripe/success)
  cancel_url?: string;       // Optionnel (défaut: /stripe/cancel)
}
```

**CheckoutSessionCreated**:
```typescript
{
  url: string;               // URL Stripe Checkout
  session_id?: string;       // ID session Stripe
}
```

**Flow paiement**:
1. Créer booking → `POST /bookings/` → status: PENDING
2. Créer session Stripe → `POST /payments/checkout-session/`
3. Rediriger vers `url` Stripe
4. Stripe redirige vers `success` ou `cancel`
5. Webhook Stripe → Backend confirme booking → status: CONFIRMED

#### 5. **Langues** (`/languages`)

| Méthode | Endpoint | Auth | Réponse | Description |
|---------|----------|------|---------|-------------|
| GET | `/languages/` | ❌ | Paginated<Language> | Liste langues |
| GET | `/languages/{id}/` | ❌ | Language | Détail langue |

**Language**:
```typescript
{
  id: number;
  code: string;        // "fr", "en", "nl", "es"
  name: string;        // "Français", "English"
  native_name: string; // "Français", "English"
}
```

---

### Format de Réponse Paginée

```typescript
interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

---

### Gestion d'Erreurs API

```typescript
// Errors standardisées
interface APIError {
  detail: string;
  code?: string;
}

// HTTP Status codes:
- 200: OK
- 201: Created
- 204: No Content
- 400: Bad Request (validation)
- 401: Unauthorized (token invalide/expiré)
- 403: Forbidden (pas les permissions)
- 404: Not Found
- 409: Conflict (ex: booking déjà confirmé)
- 500: Internal Server Error
```

**Refresh automatique sur 401**:
```typescript
// auth.interceptor.ts
1. Requête échoue avec 401
2. Interceptor tente refresh
3. Si refresh OK → rejoue requête avec nouveau token
4. Si refresh échoue → clear tokens + throw error
```

---

## 🐛 Bugs Potentiels

### 🔴 Critiques

#### 1. **Route Bookings Non Protégée**
**Localisation**: `app.routes.ts:54`
```typescript
// ❌ ACTUEL
{ path: 'bookings', loadComponent: ... }

// ✅ FIX
{
  path: 'bookings',
  canActivate: [authGuard],  // ← AJOUTER
  loadComponent: ...
}
```

### 🟡 Importants

#### 2. **Console.log en Production**
**Localisation**: Multiple fichiers
```typescript
// ❌ PROBLÈME
console.log('Naviguer vers événements');
console.error('Error while fetching events:', err);

// ✅ FIX
import { LoggerService } from '@core/services';
this.logger.debug('Naviguer vers événements');
this.logger.error('Error while fetching events', err);
```

#### 3. **Pas de Gestion de Subscriptions**
**Localisation**: `home.component.ts:50`, `events-list.component.ts:60`
```typescript
// ❌ PROBLÈME (Memory leak potentiel)
this.languagesApiService.list().subscribe(...) // Pas unsubscribe

// ✅ FIX 1: pipe + take(1)
this.languagesApiService.list().pipe(take(1)).subscribe(...)

// ✅ FIX 2: DestroyRef
private destroyRef = inject(DestroyRef);
const sub = this.languagesApiService.list().subscribe(...);
this.destroyRef.onDestroy(() => sub.unsubscribe());
```

#### 4. **Typo dans Variable**
**Localisation**: `register.component.ts:31`
```typescript
// ❌ TYPO
cuurenTab = 0;

// ✅ FIX
currentTab = 0;
```

### 🟢 Mineurs

#### 5. **Imports Non Utilisés**
**Localisation**: `home.component.ts`
```typescript
// ❌ Non utilisés
import { SearchBarComponent, FilterConfig, GenericSearch } from '...';
private readonly i18n = inject(I18nService);
private loader = inject(BlockingSpinnerService);
```

**Impact**: Bundle légèrement plus gros (mais tree-shaking devrait gérer)

#### 6. **Routes Dupliquées login/register**
**Localisation**: `app.routes.ts:46-52`
```typescript
// Déjà dans auth/ aux lignes 35-41
{ path: 'register', loadComponent: ... }  // ← Doublon
{ path: 'login', loadComponent: ... }     // ← Doublon
```

**Impact**: Aucun (fonctionne), mais redondant

---

## ✅ Bonnes Pratiques Détectées

1. ✅ **Standalone Components** partout
2. ✅ **Signals API** pour réactivité
3. ✅ **ChangeDetectionStrategy.OnPush** sur composants
4. ✅ **Lazy Loading** sur toutes les features
5. ✅ **Guards** pour auth/guest
6. ✅ **Interceptor** pour token injection
7. ✅ **DomSanitizer** pour innerHTML
8. ✅ **Try-catch** autour de localStorage
9. ✅ **HttpParams** pour query strings (pas de string concatenation)
10. ✅ **Observable** patterns (pipe, operators)

---

## 📊 Recommandations Prioritaires

### 🔴 Haute Priorité

1. **Ajouter `authGuard` sur `/bookings`**
   - Fichier: `app.routes.ts:54`
   - Temps: 2 minutes
   - Impact: Sécurité critique

2. **Supprimer/Remplacer console.log**
   - Créer service Logger
   - Remplacer dans toutes les features
   - Temps: 15 minutes

### 🟡 Moyenne Priorité

3. **Gérer subscriptions correctement**
   - Ajouter `take(1)` ou `DestroyRef`
   - Prévenir memory leaks
   - Temps: 20 minutes

4. **Corriger typo `cuurenTab`**
   - Fichier: `register.component.ts:31`
   - Temps: 1 minute

5. **Ajouter Content Security Policy**
   - Configuration backend (headers HTTP)
   - Temps: 10 minutes

### 🟢 Basse Priorité

6. **Nettoyer imports non utilisés**
   - Linter devrait détecter
   - Temps: 5 minutes

7. **Supprimer routes dupliquées**
   - Garder seulement `/auth/login` et `/auth/register`
   - Supprimer `/:lang/login` et `/:lang/register`
   - Temps: 2 minutes

---

## 🎯 Score Final

| Catégorie | Score | Commentaire |
|-----------|-------|-------------|
| **Sécurité Auth** | 9/10 | Excellente implémentation JWT |
| **Protection XSS** | 10/10 | DomSanitizer correct |
| **Guards** | 7/10 | Manque authGuard sur bookings |
| **API Design** | 9/10 | RESTful, bien typé |
| **Gestion Erreurs** | 8/10 | Interceptor refresh bon, quelques console.log |
| **Code Quality** | 8.5/10 | Bonne architecture, quelques optimisations possibles |

### **Score Global: 8.5/10** ✅

---

## 📝 Checklist de Déploiement

Avant de déployer en production:

- [ ] Ajouter `authGuard` sur `/bookings`
- [ ] Remplacer tous les `console.log` par Logger service
- [ ] Configurer `environment.prod.ts` avec URL API production
- [ ] Activer Content Security Policy (backend)
- [ ] Vérifier tous les `.subscribe()` pour unsubscribe
- [ ] Tester refresh token sur tous endpoints protégés
- [ ] Tester toutes les routes avec/sans auth
- [ ] Vérifier CORS configuration (backend)
- [ ] Activer HTTPS only (production)
- [ ] Tester paiement Stripe en mode TEST complet

---

**Date**: 20 octobre 2025
**Prochain audit recommandé**: Après déploiement production
