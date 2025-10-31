# 📚 Storybook - Conversa Design System

## Lancer Storybook

```bash
cd frontend
npm run storybook
```

Ouvre [http://localhost:6006](http://localhost:6006)

## Ce que vous verrez

- **UI/Button** - Toutes les variantes de boutons
- **UI/Badge** - Badges avec variantes et tailles
- **UI/Card** - Cartes avec différents styles

## Fonctionnalités

### Addon Accessibilité (a11y)
- Onglet "Accessibility" affiche les violations WCAG
- Tests automatiques de contraste, labels, ARIA

### Controls
- Modifier les props en direct
- Tester toutes les variantes

### Docs
- Documentation auto-générée
- Exemples de code

## Ajouter une Story

```typescript
// mon-composant.stories.ts
import type { Meta, StoryObj } from '@storybook/angular';
import { MonComposant } from './mon-composant.component';

const meta: Meta<MonComposant> = {
  title: 'UI/MonComposant',
  component: MonComposant,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<MonComposant>;

export const Default: Story = {
  render: () => ({
    template: '<mon-composant></mon-composant>',
  }),
};
```
