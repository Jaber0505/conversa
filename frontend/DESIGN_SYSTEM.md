# 🎨 Conversa Design System

Guide complet du système de design de Conversa - Une plateforme d'échange linguistique moderne et accessible.

---

## 📋 Table des Matières

1. [Architecture](#architecture)
2. [Design Tokens](#design-tokens)
3. [Composants UI](#composants-ui)
4. [Animations](#animations)
5. [Grid System](#grid-system)
6. [Accessibilité](#accessibilité)
7. [Performance](#performance)
8. [Documentation Storybook](#documentation-storybook)
9. [Guide d'utilisation](#guide-dutilisation)

---

## 🏗️ Architecture

### Structure des Composants

```
frontend/src/app/shared/
├── ui/                    # Composants atomiques
│   ├── button/
│   ├── badge/
│   ├── card/
│   └── spinner/
├── forms/                 # Contrôles de formulaire
│   ├── input/
│   ├── select/
│   ├── multi-select/
│   ├── search-bar/
│   └── form-field/
├── layout/                # Composants de mise en page
│   ├── container/
│   ├── section/
│   ├── grid/
│   ├── advanced-grid/
│   ├── grid-item/
│   └── headline-bar/
├── content/               # Composants de contenu
│   ├── event-card/
│   └── category-card/
├── components/            # Composants features
│   ├── site-header/
│   ├── language-popover/
│   ├── search-panel/
│   └── modals/
└── directives/            # Directives réutilisables
    ├── animations/
    ├── a11y/
    └── performance/
```

### Principes

- **Atomic Design** : Composants du plus petit au plus complexe
- **Standalone Components** : Tous les composants utilisent l'API standalone
- **OnPush Strategy** : Optimisation des performances par défaut
- **Type Safety** : TypeScript strict pour tous les composants
- **Barrel Exports** : Organisation via fichiers index.ts

---

## 🎨 Design Tokens

### Couleurs

#### Palette Principale

```scss
--color-primary: #F25F5C;   // Corail - CTA principal
--color-secondary: #5B5F97; // Violet - Actions secondaires
--color-tertiary: #70C1B3;  // Menthe - Success/Badges
```

#### Couleurs Sémantiques

```scss
--color-success: #70C1B3;   // Vert menthe
--color-danger: #FF6B6B;    // Rouge
--color-warning: #f59e0b;   // Orange
--color-info: #3b82f6;      // Bleu
```

#### Neutres

```scss
--color-bg: #F7F7F7;        // Fond principal
--color-text: #333333;      // Texte principal
--color-muted: #E5E5E5;     // Éléments désactivés
```

### Espacement

Échelle basée sur 4px (1rem = 16px) :

```scss
--space-1: 4px;    // 0.25rem
--space-2: 8px;    // 0.5rem
--space-3: 12px;   // 0.75rem
--space-4: 16px;   // 1rem
--space-5: 20px;   // 1.25rem
--space-6: 24px;   // 1.5rem
--space-8: 32px;   // 2rem
--space-10: 40px;  // 2.5rem
--space-12: 48px;  // 3rem
```

### Typographie

#### Tailles de Police

```scss
--fs-xs: 0.75rem;   // 12px
--fs-sm: 0.875rem;  // 14px
--fs-md: 1rem;      // 16px
--fs-lg: 1.125rem;  // 18px
--fs-xl: 1.25rem;   // 20px
--fs-2xl: 1.5rem;   // 24px
--fs-3xl: 1.875rem; // 30px
--fs-4xl: 2.25rem;  // 36px
--fs-5xl: 3rem;     // 48px
```

#### Poids de Police

```scss
--fw-light: 300;
--fw-normal: 400;
--fw-medium: 500;
--fw-semibold: 600;
--fw-bold: 700;
```

### Breakpoints

Mobile-first responsive design :

```scss
--bp-xs: 375px;   // Small phones
--bp-sm: 640px;   // Phones
--bp-md: 768px;   // Tablets
--bp-lg: 1024px;  // Desktop
--bp-xl: 1280px;  // Large desktop
--bp-2xl: 1536px; // Extra large
```

### Ombres

```scss
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-base: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1);
--shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.15);
```

### Border Radius

```scss
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px; // Pill shape
```

---

## 🧩 Composants UI

### Button

Bouton versatile avec 4 variantes et 3 tailles.

```html
<!-- Primary (défaut) -->
<shared-button variant="primary">Enregistrer</shared-button>

<!-- Outline -->
<shared-button variant="outline">Annuler</shared-button>

<!-- Accent -->
<shared-button variant="accent">Action spéciale</shared-button>

<!-- Danger -->
<shared-button variant="danger">Supprimer</shared-button>

<!-- Tailles -->
<shared-button size="sm">Petit</shared-button>
<shared-button size="md">Moyen</shared-button>
<shared-button size="lg">Grand</shared-button>

<!-- Pleine largeur -->
<shared-button [block]="true">Pleine largeur</shared-button>

<!-- Avec routerLink -->
<shared-button routerLink="/events">Voir les événements</shared-button>
```

### Badge

Petites étiquettes pour statuts et catégories.

```html
<!-- Variantes -->
<shared-badge variant="primary">Primary</shared-badge>
<shared-badge variant="success">Actif</shared-badge>
<shared-badge variant="danger">Inactif</shared-badge>

<!-- Tons -->
<shared-badge tone="soft">Soft</shared-badge>
<shared-badge tone="solid">Solid</shared-badge>
<shared-badge tone="outline">Outline</shared-badge>

<!-- Tailles -->
<shared-badge size="sm">12</shared-badge>
<shared-badge size="md">Nouveau</shared-badge>
```

### Card

Conteneur flexible pour grouper du contenu.

```html
<shared-card [tone]="'soft'" [padded]="true" [clickable]="false">
  <!-- Image (optionnel) -->
  <div class="card__media">
    <img src="image.jpg" alt="Description">
  </div>

  <!-- En-tête (optionnel) -->
  <div class="card__header">
    Titre de la carte
  </div>

  <!-- Contenu principal -->
  <div class="card__body">
    <p>Contenu de la carte...</p>
  </div>

  <!-- Footer (optionnel) -->
  <div class="card__footer">
    <shared-button size="sm">Action</shared-button>
  </div>
</shared-card>
```

---

## ✨ Animations

### Directives d'Animation

#### animate - Animation simple

```html
<!-- Fade in up au chargement -->
<div animate="fadeInUp" [animateDuration]="'fast'">
  Contenu animé
</div>

<!-- Scale in avec délai -->
<div animate="scaleIn" [animateDelay]="200">
  Apparition avec délai
</div>
```

#### animateOnScroll - Animation au scroll

```html
<!-- Apparaît quand visible dans le viewport -->
<div animateOnScroll="fadeInUp" [animateThreshold]="0.2">
  Apparaît en scrollant
</div>

<!-- Répéter l'animation à chaque passage -->
<div animateOnScroll="slideInLeft" [animateRepeat]="true">
  Animation répétée
</div>
```

### Animations Disponibles

**Entrées** : fadeIn, fadeInUp, fadeInDown, fadeInLeft, fadeInRight, scaleIn, slideInUp, slideInDown

**Sorties** : fadeOut, fadeOutUp, fadeOutDown, scaleOut

**Feedback** : pulse, bounce, shake, wiggle, heartbeat

**Loading** : spin, spinReverse, shimmer

### Keyframes Personnalisées

```scss
@import 'styles/tokens/animations';

.my-element {
  animation: fadeInUp var(--duration-normal) var(--ease-out-expo);
}
```

---

## 📐 Grid System

### Système de Grille CSS

Classes utilitaires pour créer des layouts complexes.

```html
<!-- Grille de 12 colonnes -->
<div class="grid grid-cols-12 gap-4">
  <div class="col-span-12 col-md-6 col-lg-4">Item 1</div>
  <div class="col-span-12 col-md-6 col-lg-4">Item 2</div>
  <div class="col-span-12 col-md-12 col-lg-4">Item 3</div>
</div>

<!-- Grille auto-responsive -->
<div class="grid grid-cols-auto-fit gap-6">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</div>

<!-- Contrôle de l'ordre -->
<div class="grid grid-cols-3 gap-4">
  <div class="order-3">Apparaît en 3e</div>
  <div class="order-1">Apparaît en 1er</div>
  <div class="order-2">Apparaît en 2e</div>
</div>
```

### Composant Advanced Grid

```html
<!-- Grille responsive avec composant -->
<shared-advanced-grid
  [cols]="1"
  [colsMd]="2"
  [colsLg]="3"
  [gap]="6"
  [alignItems]="'center'">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</shared-advanced-grid>
```

### Composant Grid Item

```html
<shared-advanced-grid [cols]="12" [gap]="4">
  <!-- Full width mobile, 50% tablet, 33% desktop -->
  <shared-grid-item [span]="12" [spanMd]="6" [spanLg]="4">
    Item responsive
  </shared-grid-item>

  <!-- Contrôle de position -->
  <shared-grid-item [start]="2" [end]="5">
    Colonnes 2 à 4
  </shared-grid-item>

  <!-- Ordre personnalisé -->
  <shared-grid-item [order]="'last'" [orderLg]="1">
    Ordre responsive
  </shared-grid-item>
</shared-advanced-grid>
```

---

## ♿ Accessibilité

### Directives A11Y

#### skipLink - Navigation rapide

```html
<!-- En haut de la page -->
<a skipLink target="#main-content">Aller au contenu principal</a>

<!-- Contenu principal -->
<main id="main-content">
  ...
</main>
```

#### autoFocus - Focus automatique accessible

```html
<!-- Focus au chargement avec délai pour lecteurs d'écran -->
<input autoFocus [autoFocusDelay]="100" placeholder="Rechercher...">
```

#### liveAnnouncer - Annonces pour lecteurs d'écran

```html
<!-- Annonce polite (non urgente) -->
<div liveAnnouncer="polite" role="status">
  {{ statusMessage }}
</div>

<!-- Annonce assertive (urgente) -->
<div liveAnnouncer="assertive" role="alert">
  {{ errorMessage }}
</div>
```

#### trapFocus - Piège à focus (modales)

```html
<div trapFocus [trapActive]="isModalOpen" [autoFocusFirst]="true">
  <h2>Titre de la modale</h2>
  <button>Action 1</button>
  <button>Action 2</button>
</div>
```

### Service LiveAnnouncer

```typescript
import { LiveAnnouncerService } from '@shared/services/live-announcer.service';

constructor(private announcer: LiveAnnouncerService) {}

onSave() {
  this.announcer.announcePolite('Sauvegarde réussie');
}

onError() {
  this.announcer.announceAssertive('Erreur lors de la sauvegarde');
}
```

### Classes CSS Accessibles

```html
<!-- Screen reader only -->
<span class="sr-only">Information pour lecteurs d'écran</span>

<!-- Focus visible uniquement au clavier -->
<a class="focus-visible-only" href="/link">Lien</a>

<!-- Touch target minimum 44x44px -->
<button class="touch-target">Petit bouton</button>
```

---

## ⚡ Performance

### Directives de Performance

#### lazyImage - Lazy loading d'images

```html
<!-- Avec placeholder -->
<img
  lazyImage
  [src]="'image-hd.jpg'"
  [placeholder]="'image-lowres.jpg'"
  alt="Description">

<!-- Avec fallback WebP -->
<img
  lazyImage
  [src]="'image.webp'"
  [fallback]="'image.jpg'"
  alt="Description">
```

#### deferLoad - Lazy loading de composants

```html
<!-- Charge le composant uniquement quand visible -->
<ng-container *deferLoad>
  <heavy-component></heavy-component>
</ng-container>

<!-- Avec paramètres personnalisés -->
<ng-container *deferLoad="{ rootMargin: '200px', threshold: 0.1 }">
  <expensive-chart></expensive-chart>
</ng-container>
```

### Virtual Scrolling

Pour listes de milliers d'items :

```html
<shared-virtual-scroll
  [items]="myLargeList"
  [itemHeight]="60"
  [visibleItems]="10"
  [bufferSize]="3"
  (nearEnd)="loadMore()">
  <ng-template #itemTemplate let-item>
    <div class="list-item">{{ item.name }}</div>
  </ng-template>
</shared-virtual-scroll>
```

### Classes CSS de Performance

```html
<!-- Skeleton loader pendant le chargement -->
<div class="skeleton-card" *ngIf="loading"></div>
<div *ngIf="!loading">Contenu chargé</div>

<!-- Content visibility pour grandes listes -->
<div class="content-auto">
  <expensive-component></expensive-component>
</div>

<!-- GPU acceleration -->
<div class="gpu-accelerated">
  Animation fluide
</div>
```

---

## 📚 Documentation Storybook

### Lancer Storybook

```bash
cd frontend
npm run storybook
```

### Créer une Story

```typescript
// button.stories.ts
import type { Meta, StoryObj } from '@storybook/angular';
import { ButtonComponent } from './button.component';

const meta: Meta<ButtonComponent> = {
  title: 'UI/Button',
  component: ButtonComponent,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<ButtonComponent>;

export const Primary: Story = {
  args: {
    variant: 'primary',
  },
};
```

---

## 🚀 Guide d'Utilisation

### Installation des Dépendances

```bash
# Storybook
npm install --save-dev @storybook/angular @storybook/addon-essentials @storybook/addon-a11y

# TypeScript strict mode
npm install --save-dev typescript@latest
```

### Importer les Styles Globaux

```scss
// styles.scss
@use 'styles/tokens' as *;
@use 'styles/mixins' as *;
@use 'styles/utilities' as *;
```

### Utiliser les Composants

```typescript
// app.component.ts
import { SHARED_UI, SHARED_LAYOUT, SHARED_FORMS } from '@shared';

@Component({
  standalone: true,
  imports: [...SHARED_UI, ...SHARED_LAYOUT, ...SHARED_FORMS],
  // ...
})
```

### Utiliser les Directives

```typescript
import { ANIMATION_DIRECTIVES, A11Y_DIRECTIVES, PERFORMANCE_DIRECTIVES } from '@shared/directives';

@Component({
  standalone: true,
  imports: [
    ...ANIMATION_DIRECTIVES,
    ...A11Y_DIRECTIVES,
    ...PERFORMANCE_DIRECTIVES,
  ],
  // ...
})
```

---

## 🎯 Bonnes Pratiques

### Accessibilité

- ✅ Toujours fournir des `alt` pour les images
- ✅ Utiliser des labels visibles pour les formulaires
- ✅ Tester avec un lecteur d'écran (NVDA, JAWS, VoiceOver)
- ✅ Garantir un contraste de 4.5:1 minimum (WCAG AA)
- ✅ Support clavier complet (Tab, Enter, Escape)

### Performance

- ✅ Lazy load des images et composants lourds
- ✅ Virtual scrolling pour listes > 100 items
- ✅ OnPush change detection par défaut
- ✅ TrackBy pour les ngFor
- ✅ Preload des routes critiques

### Responsive Design

- ✅ Mobile-first approach
- ✅ Tester sur tous les breakpoints
- ✅ Touch targets minimum 44x44px
- ✅ Typographie fluide avec clamp()

### Maintenabilité

- ✅ Composants atomiques réutilisables
- ✅ Types TypeScript stricts
- ✅ Documentation Storybook à jour
- ✅ Tests unitaires pour composants critiques

---

## 📊 Checklist de Qualité

Avant de merger du code :

- [ ] Tests passent (unit + e2e)
- [ ] Accessibilité validée (audit Lighthouse)
- [ ] Performance acceptable (Lighthouse > 90)
- [ ] Responsive testé (mobile, tablet, desktop)
- [ ] Story Storybook créée/mise à jour
- [ ] Types TypeScript corrects
- [ ] Pas de console.log/debugger

---

## 🤝 Contribution

Pour contribuer au Design System :

1. Créer un composant dans `shared/`
2. Ajouter les types TypeScript
3. Créer les stories Storybook
4. Tester l'accessibilité (a11y addon)
5. Documenter dans ce README
6. Soumettre une PR

---

## 📞 Support

- 📖 Documentation : `npm run storybook`
- 🐛 Issues : GitHub Issues
- 💬 Questions : Slack #frontend-conversa

---

**Version** : 1.0.0
**Dernière mise à jour** : {{ DATE }}
**Maintenu par** : Équipe Frontend Conversa
