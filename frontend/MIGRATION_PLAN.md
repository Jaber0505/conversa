# 📋 Plan de Migration - Frontend Conversa

## ✅ **ÉTAPE 1 : PRÉPARATION (Terminé)**

- [x] Créer structure de dossiers `core/features/shared`
- [x] Nettoyer fichier `fr.json` (fusionner doublons "common")
- [x] Documenter architecture (`ARCHITECTURE.md`)

---

## 🔄 **ÉTAPE 2 : NETTOYAGE DU CODE (30 min)**

### **A. Supprimer debugger/console.log**

**Fichiers à nettoyer** :
```bash
# Trouver tous les debugger
frontend/src/app/features/home/home.component.ts:57      → debugger;
frontend/src/app/event-list-mock/event-list-mock.ts:143 → debugger;

# Console.log à supprimer
frontend/src/app/features/home/home.component.ts:69-70
```

**Action** :
1. Ouvrir chaque fichier
2. Supprimer les lignes contenant `debugger` et `console.log`
3. Vérifier qu'il compile : `ng build`

---

## 📦 **ÉTAPE 3 : MIGRATION DES COMPOSANTS (2h)**

### **Principe** : Déplacer sans casser l'existant

### **A. Features - Auth**

**Fichiers existants** :
```
src/app/
├── login-page/                    → À DÉPLACER
│   ├── login-page.ts              → features/auth/login/login.component.ts
│   ├── login-page.html            → features/auth/login/login.component.html
│   └── login-page.scss            → features/auth/login/login.component.scss
│
└── upload/register-page/          → À DÉPLACER
    ├── register-page.ts           → features/auth/register/register.component.ts
    ├── register-page.html         → features/auth/register/register.component.html
    └── register-page.scss         → features/auth/register/register.component.scss
```

**Actions** :
```bash
# 1. Copier login
cp src/app/login-page/login-page.ts src/app/features/auth/login/login.component.ts
cp src/app/login-page/login-page.html src/app/features/auth/login/login.component.html
cp src/app/login-page/login-page.scss src/app/features/auth/login/login.component.scss

# 2. Copier register
cp src/app/upload/register-page/register-page.ts src/app/features/auth/register/register.component.ts
cp src/app/upload/register-page/register-page.html src/app/features/auth/register/register.component.html
cp src/app/upload/register-page/register-page.scss src/app/features/auth/register/register.component.scss

# 3. Renommer classes dans les fichiers copiés
# Ouvrir features/auth/login/login.component.ts
# Renommer : LoginPageComponent → LoginComponent
# Renommer : selector: 'app-login-page' → selector: 'app-login'

# 4. Mettre à jour app.routes.ts
```

**Changements dans `app.routes.ts`** :
```typescript
// AVANT
{ path: 'login', component: LoginPageComponent },
{ path: 'register', component: RegisterPageComponent },

// APRÈS
{
  path: 'login',
  loadComponent: () => import('./features/auth/login/login.component')
    .then(m => m.LoginComponent)
},
{
  path: 'register',
  loadComponent: () => import('./features/auth/register/register.component')
    .then(m => m.RegisterComponent)
},
```

---

### **B. Features - Events**

**Fichiers existants** :
```
src/app/
└── event-list-mock/               → À RENOMMER
    ├── event-list-mock.ts         → features/events/list/events-list.component.ts
    ├── event-list-mock.html       → features/events/list/events-list.component.html
    └── event-list-mock.scss       → features/events/list/events-list.component.scss
```

**Actions** :
```bash
# 1. Copier dans features/events/list/
cp src/app/event-list-mock/event-list-mock.ts src/app/features/events/list/events-list.component.ts
cp src/app/event-list-mock/event-list-mock.html src/app/features/events/list/events-list.component.html
cp src/app/event-list-mock/event-list-mock.scss src/app/features/events/list/events-list.component.scss

# 2. Renommer classe
# Ouvrir features/events/list/events-list.component.ts
# Renommer : EventListMockComponent → EventsListComponent
# Renommer : selector: 'app-event-list-mock' → selector: 'app-events-list'

# 3. Mettre à jour routes
```

**Changements dans `app.routes.ts`** :
```typescript
// AVANT
{ path: 'events', component: EventListMockComponent },

// APRÈS
{
  path: 'events',
  loadComponent: () => import('./features/events/list/events-list.component')
    .then(m => m.EventsListComponent)
},
```

---

### **C. Features - Bookings**

**Fichiers existants** :
```
src/app/
└── booking-page/                  → À DÉPLACER
    ├── booking-page.ts            → features/bookings/my-bookings/my-bookings.component.ts
    ├── booking-page.html          → features/bookings/my-bookings/my-bookings.component.html
    └── booking-page.scss          → features/bookings/my-bookings/my-bookings.component.scss
```

**Actions** :
```bash
# 1. Copier
cp src/app/booking-page/booking-page.ts src/app/features/bookings/my-bookings/my-bookings.component.ts
cp src/app/booking-page/booking-page.html src/app/features/bookings/my-bookings/my-bookings.component.html
cp src/app/booking-page/booking-page.scss src/app/features/bookings/my-bookings/my-bookings.component.scss

# 2. Renommer classe
# BookingsListComponent → MyBookingsComponent
# selector: 'app-bookings-list' → 'app-my-bookings'

# 3. Mettre à jour routes
```

---

### **D. Features - Home**

**Fichiers existants** :
```
src/app/features/home/             ✅ DÉJÀ AU BON ENDROIT
├── home.component.ts
├── home.component.html
└── home.component.scss
```

**Actions** :
- Juste nettoyer les `debugger` et `console.log`

---

## 🎨 **ÉTAPE 4 : CRÉER LE DESIGN SYSTEM (3h)**

### **A. Tokens SCSS**

**Créer** : `src/styles/tokens/`

```bash
mkdir -p src/styles/tokens
```

**Fichiers à créer** :
1. `_colors.scss` - Palette couleurs
2. `_spacing.scss` - Spacing scale
3. `_typography.scss` - Fonts, sizes
4. `_breakpoints.scss` - Mobile/Tablet/Desktop
5. `_shadows.scss` - Élévations

---

### **B. Mixins Responsive**

**Créer** : `src/styles/mixins/_responsive.scss`

```scss
@mixin mobile {
  @media (max-width: 767px) { @content; }
}

@mixin tablet {
  @media (min-width: 768px) and (max-width: 1023px) { @content; }
}

@mixin desktop {
  @media (min-width: 1024px) { @content; }
}
```

---

### **C. Composants UI Atoms**

**À créer** :
1. `shared/ui/atoms/button/` - Bouton avec variants
2. `shared/ui/atoms/badge/` - Badge avec couleurs
3. `shared/ui/atoms/spinner/` - Loading spinner

---

## ⚡ **ÉTAPE 5 : LAZY LOADING (1h)**

**Déjà fait dans ÉTAPE 3** si vous avez suivi les changements de routes.

**Vérifier bundle** :
```bash
ng build --configuration production
```

**Attendu** :
```
main.js       : ~350 KB
events-lazy.js: ~120 KB
auth-lazy.js  : ~60 KB
```

---

## 📱 **ÉTAPE 6 : RESPONSIVE MOBILE (2h)**

### **A. Viewport Meta**

**Vérifier dans `src/index.html`** :
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

### **B. Appliquer mixins responsive**

**Sur chaque composant** :
```scss
.event-card {
  @include mobile {
    padding: 1rem;
  }

  @include tablet {
    padding: 1.5rem;
  }

  @include desktop {
    padding: 2rem;
  }
}
```

---

## ✅ **ÉTAPE 7 : TESTS & VALIDATION (1h)**

### **A. Vérifier compilation**
```bash
ng build
```

### **B. Tester workflow complet**
1. Démarrer app : `ng serve`
2. Tester navigation :
   - Home → Events → Detail
   - Register → Login
   - Bookings (si connecté)
3. Tester changement de langue (FR/EN/NL)

### **C. Vérifier mobile**
1. Ouvrir DevTools (F12)
2. Mode responsive (Ctrl+Shift+M)
3. Tester iPhone SE (375px)
4. Tester iPad (768px)

---

## 🗑️ **ÉTAPE 8 : NETTOYAGE FINAL (30 min)**

### **Supprimer anciens dossiers**

**Une fois que TOUT fonctionne** :
```bash
# Supprimer anciens dossiers
rm -rf src/app/login-page
rm -rf src/app/upload/register-page
rm -rf src/app/event-list-mock
rm -rf src/app/booking-page
```

---

## 📊 **RÉCAPITULATIF**

| Étape | Temps estimé | Statut |
|-------|--------------|--------|
| 1. Préparation | 30 min | ✅ Terminé |
| 2. Nettoyage code | 30 min | ⏳ En cours |
| 3. Migration composants | 2h | ⏳ À faire |
| 4. Design system | 3h | ⏳ À faire |
| 5. Lazy loading | 1h | ⏳ À faire |
| 6. Responsive | 2h | ⏳ À faire |
| 7. Tests | 1h | ⏳ À faire |
| 8. Nettoyage | 30 min | ⏳ À faire |
| **TOTAL** | **10-11h** | |

---

## 🎯 **Prochaines Actions**

1. **Nettoyer** debugger/console.log (ÉTAPE 2)
2. **Migrer** composants auth (ÉTAPE 3.A)
3. **Tester** que ça compile
4. **Continuer** avec events, bookings, etc.

**Prêt à commencer l'ÉTAPE 2 ?** 🚀
