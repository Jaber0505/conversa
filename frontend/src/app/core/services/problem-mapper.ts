// core/services/problem-mapper.ts
import { FormGroup, AbstractControl } from '@angular/forms';
import { Problem } from '../models/problem.model';

export function applyProblemToForm(form: FormGroup, problem?: Problem, map?: Record<string,string>) {
  if (!problem?.fields) return;
  const m = map ?? {};
  const getCtrl = (apiField: string): AbstractControl | null => {
    const path = m[apiField] ?? apiField; // ex: 'email' -> 'credentials.email'
    return form.get(path);
  };
  for (const f of problem.fields) {
    const c = getCtrl(f.field);
    if (c) c.setErrors({ ...(c.errors ?? {}), server: f.code || 'INVALID' });
  }
}
