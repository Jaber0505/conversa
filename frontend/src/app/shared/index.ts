export * from './ui';
export * from './layout';
export * from './forms';
export * from './content';

import { SHARED_UI } from './ui';
import { SHARED_LAYOUT } from './layout';
import { SHARED_FORMS } from './forms';
import { SHARED_CONTENT } from './content';

export const SHARED_IMPORTS = [
  ...SHARED_UI,
  ...SHARED_LAYOUT,
  ...SHARED_FORMS,
  ...SHARED_CONTENT,
] as const;
