# 🏗️ Architecture Frontend - Conversa

## 📐 **Pattern : Feature-Sliced Design + Atomic Design**

Cette architecture combine **2 patterns modernes** pour maximiser la modularité, la clarté et la scalabilité.

---

## 📂 **Structure des Dossiers**

```
src/app/
│
├── core/                           # 🔒 SINGLETON (Services globaux)
│   ├── auth/                       # Authentification
│   │   ├── guards/
│   │   │   ├── auth.guard.ts       # Protège routes privées
│   │   │   └── guest.guard.ts      # Redirige si déjà connecté
│   │   ├── services/
│   │   │   ├── auth.service.ts     # Login/Logout/Register
│   │   │   └── token.service.ts    # Gestion JWT
│   │   └── interceptors/
│   │       └── auth.interceptor.ts # Ajoute JWT aux requêtes
│   │
│   ├── api/                        # Services API (1 par resource)
│   │   ├── base-api.service.ts     # Classe abstraite commune
│   │   ├── events-api.service.ts   # CRUD Events
│   │   ├── bookings-api.service.ts # CRUD Bookings
│   │   ├── payments-api.service.ts # Stripe
│   │   └── languages-api.service.ts
│   │
│   ├── state/                      # State Management (Signals)
│   │   ├── auth.state.ts           # État auth global
│   │   ├── events.state.ts         # Cache events
│   │   └── ui.state.ts             # UI state (modal, sidebar)
│   │
│   ├── i18n/                       # Internationalisation
│   │   ├── services/
│   │   │   ├── i18n.service.ts     # Service traduction
│   │   │   └── lang.service.ts     # Gestion langue active
│   │   ├── guards/
│   │   │   └── language-url.guard.ts
│   │   ├── pipes/
│   │   │   └── translate.pipe.ts   # {{ 'key' | t }}
│   │   └── config/
│   │       └── languages.config.ts  # Langues supportées
│   │
│   └── config/
│       ├── api.config.ts           # API_URL, constantes
│       └── app.config.ts           # Providers globaux
│
├── features/                       # 📦 MODULES MÉTIER (lazy-loaded)
│   │
│   ├── home/                       # 🏠 Page d'accueil
│   │   ├── home.component.ts
│   │   ├── home.component.html
│   │   ├── home.component.scss
│   │   └── components/             # Composants spécifiques home
│   │       ├── hero-section/
│   │       ├── search-section/
│   │       └── stats-section/
│   │
│   ├── auth/                       # 🔐 Authentification
│   │   ├── login/
│   │   │   ├── login.component.ts
│   │   │   ├── login.component.html
│   │   │   └── login.component.scss
│   │   └── register/
│   │       ├── register.component.ts
│   │       ├── register.component.html
│   │       ├── register.component.scss
│   │       └── components/
│   │           └── language-selector/
│   │
│   ├── events/                     # 📅 Événements
│   │   ├── list/                   # Page liste
│   │   │   ├── events-list.component.ts
│   │   │   ├── events-list.component.html
│   │   │   ├── events-list.component.scss
│   │   │   └── components/
│   │   │       ├── events-filters/
│   │   │       └── events-empty-state/
│   │   │
│   │   └── detail/                 # Page détail
│   │       ├── event-detail.component.ts
│   │       ├── event-detail.component.html
│   │       ├── event-detail.component.scss
│   │       └── components/
│   │           ├── event-info-card/
│   │           └── booking-button/
│   │
│   └── bookings/                   # 🎟️ Réservations
│       └── my-bookings/
│           ├── my-bookings.component.ts
│           ├── my-bookings.component.html
│           ├── my-bookings.component.scss
│           └── components/
│               ├── booking-card/
│               └── cancel-modal/
│
└── shared/                         # 🧩 COMPOSANTS RÉUTILISABLES
    │
    ├── ui/                         # Design System (Atomic Design)
    │   ├── atoms/                  # Composants de base
    │   │   ├── button/
    │   │   ├── badge/
    │   │   ├── icon/
    │   │   ├── avatar/
    │   │   └── spinner/
    │   │
    │   ├── molecules/              # Combinaisons
    │   │   ├── form-field/
    │   │   ├── search-input/
    │   │   ├── language-select/
    │   │   └── card/
    │   │
    │   └── organisms/              # Composants complexes
    │       ├── modal/
    │       ├── navbar/
    │       └── footer/
    │
    ├── layouts/                    # Templates de page
    │   ├── main-layout/            # Navbar + Content + Footer
    │   ├── auth-layout/            # Layout minimal pour login
    │   └── blank-layout/           # Juste le contenu
    │
    ├── directives/
    │   ├── click-outside.directive.ts
    │   ├── lazy-load-image.directive.ts
    │   └── swipe.directive.ts
    │
    ├── pipes/
    │   ├── date-ago.pipe.ts
    │   └── currency-format.pipe.ts
    │
    └── utils/
        ├── date.utils.ts
        └── responsive.utils.ts
```

---

## 🎯 **Règles d'Architecture**

### **LAYER 1: CORE (Singleton)**

✅ **Autorisé** :
- Services `@Injectable({ providedIn: 'root' })`
- Guards, Interceptors
- Configuration globale

❌ **Interdit** :
- Composants UI
- Logique métier spécifique

### **LAYER 2: FEATURES (Domaines métier)**

✅ **Autorisé** :
- Importer depuis `@core/*`
- Importer depuis `@shared/*`
- Composants spécifiques au feature

❌ **Interdit** :
- Importer depuis un autre feature
- Services singleton (mettre dans core/)

### **LAYER 3: SHARED (Composants purs)**

✅ **Autorisé** :
- Composants avec `@Input()/@Output()` uniquement
- Pipes, Directives réutilisables
- Utilitaires purs (pas de side-effects)

❌ **Interdit** :
- Importer depuis `@core/*` ou `@features/*`
- Services avec state
- Appels API

---

## 🔄 **Flux de Données**

```
USER → ROUTER → FEATURE COMPONENT → CORE SERVICE → API → BACKEND
                      ↓
                  Uses SHARED UI Components
```

**Exemple** :
```typescript
// ✅ BON
export class EventsListComponent {
  private eventsApi = inject(EventsApiService);  // depuis @core

  // Utilise shared/ui/button
  template: `<ui-button (clicked)="book()">Réserver</ui-button>`
}

// ❌ INTERDIT
export class ButtonComponent {
  private eventsApi = inject(EventsApiService);  // ❌ Shared ne peut pas utiliser core
}
```

---

## 📝 **Conventions de Nommage**

### **Fichiers**
- **Composants** : `events-list.component.ts`
- **Services** : `events-api.service.ts`
- **Guards** : `auth.guard.ts`
- **Pipes** : `translate.pipe.ts`

### **Classes**
- **Composants** : `EventsListComponent`
- **Services** : `EventsApiService`
- **Guards** : `AuthGuard`

### **Sélecteurs**
- **Shared UI** : `ui-button`, `ui-badge`
- **Features** : `events-list`, `booking-card`

---

## 🎨 **Design System (Atomic Design)**

```
ATOMS → MOLECULES → ORGANISMS
  ↓         ↓            ↓
Button    FormField   EventCard
Badge     SearchBar   Modal
Icon      Card        Navbar
```

**Exemple** :
```typescript
// Atom
<ui-button label="Cliquer" />

// Molecule
<ui-form-field label="Email">
  <input type="email" />
</ui-form-field>

// Organism
<ui-modal [open]="true">
  <ui-button>Fermer</ui-button>
</ui-modal>
```

---

## 🚀 **Performance (Lazy Loading)**

```typescript
// app.routes.ts
export const routes: Routes = [
  // ✅ Eager (chargé au démarrage)
  { path: '', component: HomeComponent },

  // ✅ Lazy (chargé à la demande)
  {
    path: 'events',
    loadComponent: () => import('./features/events/list/events-list.component')
      .then(m => m.EventsListComponent)
  }
];
```

**Impact** :
- Bundle initial : 350KB (au lieu de 1MB)
- Pages suivantes : chargées à la demande

---

## ✅ **Checklist Qualité**

### **Code**
- [ ] Pas de `debugger`
- [ ] Pas de `console.log` non nettoyés
- [ ] Imports organisés (core → shared → local)
- [ ] Types TypeScript stricts

### **Architecture**
- [ ] Features isolés (pas de dépendances croisées)
- [ ] Shared sans dépendances externes
- [ ] Services dans core/ (pas dans features/)

### **Performance**
- [ ] Lazy loading activé
- [ ] OnPush change detection où possible
- [ ] trackBy pour *ngFor

### **UX/UI**
- [ ] Mobile-first (responsive)
- [ ] Touch targets ≥ 44px
- [ ] Animations fluides
- [ ] Loading states

---

## 📚 **Documentation**

- [README Backend](../../backend/README.md)
- [API Documentation](http://localhost:8000/api/docs/)
- [Traductions i18n](./src/assets/i18n/)

---

## 🎓 **Pour le Jury**

Cette architecture est basée sur :
- **Feature-Sliced Design** (organisation par domaine métier)
- **Atomic Design** (design system modulaire)
- **Angular Best Practices 2025** (Standalone Components, Signals)

**Avantages** :
- ✅ Scalable (ajout de features facile)
- ✅ Maintenable (code isolé par layer)
- ✅ Testable (composants purs)
- ✅ Performant (lazy loading)
