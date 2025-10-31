import type { Meta, StoryObj } from '@storybook/angular';
import { BadgeComponent } from './badge.component';

const meta: Meta<BadgeComponent> = {
  title: 'UI/Badge',
  component: BadgeComponent,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<BadgeComponent>;

export const Primary: Story = {
  render: () => ({
    template: '<shared-badge variant="primary">Badge</shared-badge>',
  }),
};

export const AllVariants: Story = {
  render: () => ({
    template: `
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        <shared-badge variant="primary">Primary</shared-badge>
        <shared-badge variant="secondary">Secondary</shared-badge>
        <shared-badge variant="accent">Accent</shared-badge>
        <shared-badge variant="success">Success</shared-badge>
        <shared-badge variant="danger">Danger</shared-badge>
        <shared-badge variant="muted">Muted</shared-badge>
      </div>
    `,
  }),
};

export const AllTones: Story = {
  render: () => ({
    template: `
      <div style="display: flex; gap: 0.5rem;">
        <shared-badge tone="soft">Soft</shared-badge>
        <shared-badge tone="solid">Solid</shared-badge>
        <shared-badge tone="outline">Outline</shared-badge>
      </div>
    `,
  }),
};

export const Sizes: Story = {
  render: () => ({
    template: `
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <shared-badge size="sm">Small</shared-badge>
        <shared-badge size="md">Medium</shared-badge>
      </div>
    `,
  }),
};
