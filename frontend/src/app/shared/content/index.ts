import { CategoryCardComponent } from './category-card/category-card.component';
import { EventCardComponent }    from './event-card/event-card.component';
import { EventActionButtonComponent } from '../components/event-action-button/event-action-button.component';

export { CategoryCardComponent } from './category-card/category-card.component';
export { EventCardComponent }    from './event-card/event-card.component';
export { EventActionButtonComponent } from '../components/event-action-button/event-action-button.component';

export const SHARED_CONTENT = [
  CategoryCardComponent,
  EventCardComponent,
  EventActionButtonComponent
] as const;
