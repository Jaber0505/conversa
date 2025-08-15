import { ButtonComponent } from './button/button.component';
import { BadgeComponent }  from './badge/badge.component';
import { CardComponent }   from './card/card.component';

export { ButtonComponent } from './button/button.component';
export { BadgeComponent }  from './badge/badge.component';
export { CardComponent }   from './card/card.component';

export const SHARED_UI = [ ButtonComponent, BadgeComponent, CardComponent ] as const;
