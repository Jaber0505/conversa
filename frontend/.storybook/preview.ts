import type { Preview } from '@storybook/angular';
import { setCompodocJson } from '@storybook/addon-docs/angular';
import { provideRouter } from '@angular/router';
import { applicationConfig } from '@storybook/angular';

// Les styles sont chargés via angular.json, pas besoin d'import ici
// import '../src/styles/styles.scss';

const preview: Preview = {
  decorators: [
    applicationConfig({
      providers: [
        provideRouter([]), // Router vide pour Storybook
      ],
    }),
  ],

  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
      expanded: true,
    },
    backgrounds: {
      options: {
        light: { name: 'light', value: '#F7F7F7' },
        white: { name: 'white', value: '#FFFFFF' },
        dark: { name: 'dark', value: '#333333' }
      }
    },
    layout: 'padded',
    docs: {
      toc: true, // Table of contents
    },
  },

  globalTypes: {
    locale: {
      name: 'Locale',
      description: 'Internationalization locale',
      defaultValue: 'fr',
      toolbar: {
        icon: 'globe',
        items: [
          { value: 'fr', title: 'Français' },
          { value: 'en', title: 'English' },
          { value: 'nl', title: 'Nederlands' },
        ],
        showName: true,
      },
    },
  },

  initialGlobals: {
    backgrounds: {
      value: 'light'
    }
  }
};

export default preview;
