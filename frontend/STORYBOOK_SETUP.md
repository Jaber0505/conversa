# 📚 Configuration Storybook pour Conversa

Ce guide vous aide à configurer Storybook pour le projet Conversa.

---

## 📦 Installation

### 1. Installer Storybook et ses addons

```bash
cd frontend

# Installer Storybook avec l'auto-configuration Angular
npx storybook@latest init

# OU installer manuellement
npm install --save-dev @storybook/angular @storybook/addon-essentials @storybook/addon-interactions @storybook/addon-links
```

### 2. Installer les addons supplémentaires

```bash
# Addon pour tester l'accessibilité
npm install --save-dev @storybook/addon-a11y

# Addon pour intégrer les designs Figma/Sketch
npm install --save-dev @storybook/addon-designs

# Addon pour les tests de composants
npm install --save-dev @storybook/test

# Compodoc pour la documentation TypeScript
npm install --save-dev @compodoc/compodoc
```

---

## ⚙️ Configuration

Les fichiers de configuration sont déjà créés dans `.storybook/` :

- `main.ts` - Configuration principale
- `preview.ts` - Configuration de l'aperçu

### Scripts package.json

Ajoutez ces scripts à votre `package.json` :

```json
{
  "scripts": {
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
    "docs:json": "compodoc -p tsconfig.json -e json -d .",
    "storybook:docs": "npm run docs:json && npm run storybook"
  }
}
```

---

## 🚀 Lancer Storybook

### Mode développement

```bash
npm run storybook
```

Ouvre Storybook sur [http://localhost:6006](http://localhost:6006)

### Avec documentation TypeScript

```bash
npm run storybook:docs
```

### Build pour production

```bash
npm run build-storybook
```

Crée un build statique dans `storybook-static/`

---

## 📝 Créer une Story

### Exemple basique

```typescript
// button.stories.ts
import type { Meta, StoryObj } from '@storybook/angular';
import { ButtonComponent } from './button.component';

const meta: Meta<ButtonComponent> = {
  title: 'UI/Button',
  component: ButtonComponent,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'outline', 'accent', 'danger'],
    },
  },
};

export default meta;
type Story = StoryObj<ButtonComponent>;

export const Primary: Story = {
  args: {
    variant: 'primary',
  },
  render: (args) => ({
    props: args,
    template: '<shared-button [variant]="variant">Mon bouton</shared-button>',
  }),
};
```

### Avec documentation MDX

```mdx
<!-- button.mdx -->
import { Meta, Canvas, Story } from '@storybook/blocks';
import * as ButtonStories from './button.stories';

<Meta of={ButtonStories} />

# Button

Le composant Button est utilisé pour les actions utilisateur.

## Usage

<Canvas of={ButtonStories.Primary} />

## Variantes

<Canvas of={ButtonStories.AllVariants} />
```

---

## 🧪 Tester l'Accessibilité

L'addon a11y est déjà configuré. Il affiche automatiquement les violations WCAG dans l'onglet "Accessibility".

### Vérifications automatiques

- Contraste des couleurs
- Labels des formulaires
- Hiérarchie des titres
- Attributs ARIA
- Navigation au clavier

### Tests manuels recommandés

```bash
# Avec un lecteur d'écran
- NVDA (Windows) - gratuit
- JAWS (Windows) - payant
- VoiceOver (Mac) - intégré
- ORCA (Linux) - gratuit

# Navigation clavier
- Tab / Shift+Tab
- Enter / Space
- Escape
- Flèches directionnelles
```

---

## 📊 Bonnes Pratiques

### Organisation des Stories

```
src/app/shared/
├── ui/
│   ├── button/
│   │   ├── button.component.ts
│   │   ├── button.component.scss
│   │   ├── button.stories.ts        ← Story
│   │   └── button.mdx               ← Documentation (optionnel)
```

### Nommage des Stories

```typescript
// ✅ Bon
title: 'UI/Button'
title: 'Forms/Input'
title: 'Layout/Grid'

// ❌ Éviter
title: 'button'
title: 'MyButton'
```

### ArgTypes détaillés

```typescript
argTypes: {
  variant: {
    control: 'select',
    options: ['primary', 'outline'],
    description: 'Style visuel du bouton',
    table: {
      defaultValue: { summary: 'primary' },
      type: { summary: 'string' },
      category: 'Appearance',
    },
  },
}
```

### Documentation complète

```typescript
/**
 * Le composant Button permet de déclencher des actions.
 *
 * ## Quand l'utiliser
 * - Actions primaires (soumettre, confirmer)
 * - Actions secondaires (annuler, retour)
 *
 * ## Accessibilité
 * - Support clavier complet
 * - Focus visible
 * - ARIA labels appropriés
 */
const meta: Meta<ButtonComponent> = {
  // ...
};
```

---

## 🎨 Thèmes Storybook

### Personnaliser le thème

Créez `.storybook/manager.ts` :

```typescript
import { addons } from '@storybook/manager-api';
import { create } from '@storybook/theming/create';

addons.setConfig({
  theme: create({
    base: 'light',
    brandTitle: 'Conversa Design System',
    brandUrl: 'https://conversa.example.com',
    brandImage: '/logo.svg',

    colorPrimary: '#F25F5C',
    colorSecondary: '#5B5F97',

    appBg: '#F7F7F7',
    appContentBg: '#FFFFFF',
    appBorderColor: '#E5E5E5',

    textColor: '#333333',
    textInverseColor: '#FFFFFF',

    barTextColor: '#333333',
    barSelectedColor: '#F25F5C',
    barBg: '#FFFFFF',
  }),
});
```

---

## 📤 Déployer Storybook

### Sur Vercel

```bash
# Build
npm run build-storybook

# Déployer
vercel storybook-static/
```

### Sur Netlify

```bash
# Build
npm run build-storybook

# netlify.toml
[build]
  command = "npm run build-storybook"
  publish = "storybook-static"
```

### Sur GitHub Pages

```bash
# Build
npm run build-storybook

# Déployer
npx gh-pages -d storybook-static
```

---

## 🔧 Dépannage

### Erreur : "Cannot find module '@storybook/angular'"

```bash
npm install --save-dev @storybook/angular
```

### Erreur : Styles non chargés

Vérifiez que `styles.scss` est importé dans `.storybook/preview.ts` :

```typescript
import '../src/styles.scss';
```

### Erreur : Composants standalone non trouvés

Assurez-vous que les composants sont exportés dans `index.ts` :

```typescript
export { ButtonComponent } from './button/button.component';
```

### Performance lente

```bash
# Désactiver les addons non nécessaires dans main.ts
addons: [
  // '@storybook/addon-interactions', // Désactivé
  '@storybook/addon-essentials',
],
```

---

## 📚 Ressources

- [Documentation Storybook](https://storybook.js.org/docs)
- [Storybook pour Angular](https://storybook.js.org/docs/angular)
- [Addon A11y](https://storybook.js.org/addons/@storybook/addon-a11y)
- [Design System Exemples](https://storybook.js.org/showcase)

---

## ✅ Checklist de Configuration

- [ ] Storybook installé
- [ ] Addons configurés (a11y, essentials)
- [ ] Scripts package.json ajoutés
- [ ] Thème personnalisé (optionnel)
- [ ] Stories créées pour composants UI
- [ ] Tests d'accessibilité passent
- [ ] Documentation à jour
- [ ] Build Storybook fonctionne
- [ ] Déploiement configuré (optionnel)

---

**Bon codage ! 🚀**
