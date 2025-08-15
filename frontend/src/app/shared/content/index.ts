import { CategoryCardComponent } from './category-card/category-card.component';
import { EventCardComponent }    from './event-card/event-card.component';

export { CategoryCardComponent } from './category-card/category-card.component';
export { EventCardComponent }    from './event-card/event-card.component';

export const SHARED_CONTENT = [ CategoryCardComponent, EventCardComponent ] as const;
