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
  render: () => ({
    template: '<shared-button variant="primary">Bouton Primary</shared-button>',
  }),
};

export const Outline: Story = {
  render: () => ({
    template: '<shared-button variant="outline">Bouton Outline</shared-button>',
  }),
};

export const Accent: Story = {
  render: () => ({
    template: '<shared-button variant="accent">Bouton Accent</shared-button>',
  }),
};

export const Danger: Story = {
  render: () => ({
    template: '<shared-button variant="danger">Supprimer</shared-button>',
  }),
};

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

export const Sizes: Story = {
  render: () => ({
    template: `
      <div style="display: flex; gap: 1rem; align-items: center;">
        <shared-button size="sm">Small</shared-button>
        <shared-button size="md">Medium</shared-button>
        <shared-button size="lg">Large</shared-button>
      </div>
    `,
  }),
};
