export * from './skip-link.directive';
export * from './auto-focus.directive';
export * from './live-announcer.directive';
export * from './trap-focus.directive';

import { SkipLinkDirective } from './skip-link.directive';
import { AutoFocusDirective } from './auto-focus.directive';
import { LiveAnnouncerDirective } from './live-announcer.directive';
import { TrapFocusDirective } from './trap-focus.directive';

export const A11Y_DIRECTIVES = [
  SkipLinkDirective,
  AutoFocusDirective,
  LiveAnnouncerDirective,
  TrapFocusDirective,
];
