import type { Meta, StoryObj } from '@storybook/angular';
import { CardComponent } from './card.component';

const meta: Meta<CardComponent> = {
  title: 'UI/Card',
  component: CardComponent,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<CardComponent>;

export const Basic: Story = {
  render: () => ({
    template: `
      <shared-card [tone]="'soft'" [padded]="true" style="max-width: 400px;">
        <div class="card__header">Titre de la carte</div>
        <div class="card__body">
          <p>Ceci est le contenu de la carte.</p>
        </div>
      </shared-card>
    `,
  }),
};

export const AllTones: Story = {
  render: () => ({
    template: `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
        <shared-card tone="soft" [padded]="true">
          <div class="card__header">Soft</div>
          <div class="card__body">Ombre légère</div>
        </shared-card>
        <shared-card tone="elevated" [padded]="true">
          <div class="card__header">Elevated</div>
          <div class="card__body">Ombre prononcée</div>
        </shared-card>
        <shared-card tone="ghost" [padded]="true">
          <div class="card__header">Ghost</div>
          <div class="card__body">Sans bordure</div>
        </shared-card>
      </div>
    `,
  }),
};

export const Clickable: Story = {
  render: () => ({
    template: `
      <shared-card [clickable]="true" [padded]="true" style="max-width: 400px;">
        <div class="card__header">Carte cliquable</div>
        <div class="card__body">
          <p>Survolez pour voir l'effet hover.</p>
        </div>
      </shared-card>
    `,
  }),
};
