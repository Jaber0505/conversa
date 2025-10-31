import type { Meta, StoryObj } from '@storybook/angular';
import { ButtonComponent } from '../src/app/shared/ui/button/button.component';

/**
 * Le composant Button est un bouton versatile avec plusieurs variantes et tailles.
 *
 * ## Quand l'utiliser
 * - Pour des actions primaires (soumettre un formulaire, confirmer)
 * - Pour des actions secondaires (annuler, retour)
 * - Pour des actions destructives (supprimer, annuler)
 *
 * ## Accessibilité
 * - Utilise des attributs ARIA appropriés
 * - Support du clavier (Enter, Space)
 * - Focus ring visible
 * - States disabled clairs
 */
const meta: Meta<ButtonComponent> = {
  title: 'UI/Button',
  component: ButtonComponent,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'outline', 'accent', 'danger'],
      description: 'Style visuel du bouton',
      table: {
        defaultValue: { summary: 'primary' },
        type: { summary: 'string' },
      },
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Taille du bouton',
      table: {
        defaultValue: { summary: 'md' },
      },
    },
    type: {
      control: 'select',
      options: ['button', 'submit', 'reset'],
      description: 'Type HTML du bouton',
      table: {
        defaultValue: { summary: 'button' },
      },
    },
  },
  args: {
    variant: 'primary',
    size: 'md',
    type: 'button',
  },
};

export default meta;
type Story = StoryObj<ButtonComponent>;

/**
 * Bouton primary - Action principale
 */
export const Primary: Story = {
  args: {
    variant: 'primary',
  },
  render: (args) => ({
    props: args,
    template: '<shared-button [variant]="variant" [size]="size" [disabled]="disabled">Bouton Primary</shared-button>',
  }),
};

/**
 * Bouton outline - Action secondaire
 */
export const Outline: Story = {
  args: {
    variant: 'outline',
  },
  render: (args) => ({
    props: args,
    template: '<shared-button [variant]="variant" [size]="size" [disabled]="disabled">Bouton Outline</shared-button>',
  }),
};

/**
 * Bouton accent - Action spéciale
 */
export const Accent: Story = {
  args: {
    variant: 'accent',
  },
  render: (args) => ({
    props: args,
    template: '<shared-button [variant]="variant" [size]="size" [disabled]="disabled">Bouton Accent</shared-button>',
  }),
};

/**
 * Bouton danger - Action destructive
 */
export const Danger: Story = {
  args: {
    variant: 'danger',
  },
  render: (args) => ({
    props: args,
    template: '<shared-button [variant]="variant" [size]="size" [disabled]="disabled">Supprimer</shared-button>',
  }),
};

/**
 * Tailles disponibles
 */
export const Sizes: Story = {
  render: () => ({
    template: `
      <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
        <shared-button size="sm">Small</shared-button>
        <shared-button size="md">Medium</shared-button>
        <shared-button size="lg">Large</shared-button>
      </div>
    `,
  }),
};

/**
 * Toutes les variantes côte à côte
 */
export const AllVariants: Story = {
  render: () => ({
    template: `
      <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
        <shared-button variant="primary">Primary</shared-button>
        <shared-button variant="outline">Outline</shared-button>
        <shared-button variant="accent">Accent</shared-button>
        <shared-button variant="danger">Danger</shared-button>
      </div>
    `,
  }),
};

/**
 * Bouton désactivé
 */
export const Disabled: Story = {
  args: {
    disabled: true,
  },
  render: (args) => ({
    props: args,
    template: '<shared-button [disabled]="disabled">Bouton désactivé</shared-button>',
  }),
};

/**
 * Bouton pleine largeur
 */
export const Block: Story = {
  args: {
    block: true,
  },
  render: (args) => ({
    props: args,
    template: '<shared-button [block]="block">Bouton pleine largeur</shared-button>',
  }),
};

/**
 * Avec routerLink
 */
export const WithRouterLink: Story = {
  render: () => ({
    template: `
      <shared-button routerLink="/events">Voir les événements</shared-button>
    `,
  }),
};

/**
 * Groupe de boutons
 */
export const ButtonGroup: Story = {
  render: () => ({
    template: `
      <div style="display: flex; gap: 0.5rem;">
        <shared-button variant="outline">Annuler</shared-button>
        <shared-button variant="primary">Enregistrer</shared-button>
      </div>
    `,
  }),
};
