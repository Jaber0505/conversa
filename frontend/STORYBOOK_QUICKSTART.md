# 🚀 Storybook - Guide Rapide

## ✅ Installation Terminée

Storybook v8.6.14 est maintenant installé avec tous les addons.

---

## 🎯 Lancer Storybook

```bash
cd frontend
npm run storybook
```

**Storybook s'ouvrira sur** : [http://localhost:6006](http://localhost:6006)

---

## 📚 Ce que Vous Verrez

Dans le menu de gauche, vous trouverez :

### UI/
- **Button** - 6 stories (Primary, Outline, Accent, Danger, Sizes, AllVariants)
- **Badge** - 4 stories (Primary, AllVariants, AllTones, Sizes)
- **Card** - 3 stories (Basic, AllTones, Clickable)

---

## 🎨 Fonctionnalités

### 1. Onglet "Canvas"
- Visualiser les composants
- Interagir en direct

### 2. Onglet "Controls" (en bas)
- Modifier les props en temps réel
- Tester toutes les combinaisons

### 3. Onglet "Accessibility"
- Tests WCAG automatiques
- Violations détectées
- Recommandations

### 4. Onglet "Actions"
- Voir les événements émis (clicks, change, etc.)

### 5. Toolbar (en haut)
- Changer l'arrière-plan
- Changer la langue (fr, en, nl)
- Mode responsive

---

## 🧪 Tester l'Accessibilité

1. Cliquer sur n'importe quelle story
2. Ouvrir l'onglet "Accessibility" (en bas)
3. Voir les violations s'il y en a
4. Consulter les recommandations

**Exemples de tests** :
- ✅ Contraste des couleurs
- ✅ Labels de formulaires
- ✅ Attributs ARIA
- ✅ Hiérarchie des titres

---

## 📖 Documentation Auto-générée

Chaque composant a sa page "Docs" avec :
- Description du composant
- Props TypeScript
- Exemples de code
- Stories interactives

---

## 🎯 Exemples d'Utilisation

### Tester un Bouton Primary
1. Menu gauche → **UI** → **Button** → **Primary**
2. Voir le bouton s'afficher
3. Ouvrir "Accessibility" → Aucune violation ✅

### Tester tous les Badges
1. Menu gauche → **UI** → **Badge** → **AllVariants**
2. Voir les 6 variantes côte à côte
3. Comparer les couleurs

### Tester une Card Clickable
1. Menu gauche → **UI** → **Card** → **Clickable**
2. Survoler la carte
3. Voir l'effet hover

---

## 🛠️ Créer une Nouvelle Story

### Exemple pour un nouveau composant Input

```typescript
// input.stories.ts
import type { Meta, StoryObj } from '@storybook/angular';
import { InputComponent } from './input.component';

const meta: Meta<InputComponent> = {
  title: 'Forms/Input',
  component: InputComponent,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<InputComponent>;

export const Text: Story = {
  render: () => ({
    template: '<shared-input type="text" label="Nom"></shared-input>',
  }),
};

export const Email: Story = {
  render: () => ({
    template: '<shared-input type="email" label="Email"></shared-input>',
  }),
};
```

---

## 📊 Build Storybook (Production)

Pour créer une version statique :

```bash
npm run build-storybook
```

Crée un dossier `storybook-static/` que vous pouvez déployer.

---

## 🐛 Dépannage

### Storybook ne démarre pas
```bash
# Vérifier les ports
netstat -ano | findstr :6006

# Tuer le processus si occupé
taskkill /PID <PID> /F

# Relancer
npm run storybook
```

### Composants non trouvés
- Vérifier que le composant est dans `shared/`
- Vérifier les imports dans la story
- Relancer Storybook

### Styles non chargés
- Vérifier que `styles.scss` est bien importé dans `.storybook/preview.ts`
- Vérifier le chemin : `import '../src/styles.scss';`

---

## 🎉 C'est Tout !

Vous avez maintenant :
- ✅ Storybook v8.6.14 installé
- ✅ 13 stories prêtes à l'emploi
- ✅ Tests d'accessibilité automatiques
- ✅ Documentation interactive

**Profitez bien ! 🚀**

---

**Pour plus de détails** : Voir [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) et [STORYBOOK_SETUP.md](STORYBOOK_SETUP.md)
