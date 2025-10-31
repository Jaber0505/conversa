import { SectionComponent }    from './section/section.component';
import { ContainerComponent }  from './container/container.component';
import { GridComponent }       from './grid/grid.component';
import { HeadlineBarComponent } from './headline-bar/headline-bar.component';
import { AdvancedGridComponent } from './advanced-grid/advanced-grid.component';
import { GridItemComponent }   from './grid-item/grid-item.component';

export { SectionComponent }    from './section/section.component';
export { ContainerComponent }  from './container/container.component';
export { GridComponent }       from './grid/grid.component';
export { HeadlineBarComponent } from './headline-bar/headline-bar.component';
export { AdvancedGridComponent } from './advanced-grid/advanced-grid.component';
export { GridItemComponent }   from './grid-item/grid-item.component';

export const SHARED_LAYOUT = [
  SectionComponent,
  ContainerComponent,
  GridComponent,
  HeadlineBarComponent,
  AdvancedGridComponent,
  GridItemComponent
] as const;
