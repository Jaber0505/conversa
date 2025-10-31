export * from './lazy-image.directive';
export * from './defer-load.directive';

import { LazyImageDirective } from './lazy-image.directive';
import { DeferLoadDirective } from './defer-load.directive';

export const PERFORMANCE_DIRECTIVES = [LazyImageDirective, DeferLoadDirective];
