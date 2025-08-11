// core/models/problem.model.ts
export type ProblemField = { field: string; code: string; params?: Record<string, unknown> };
export type Problem = {
  type?: string;
  title?: string;
  status: number;
  detail?: string;
  code: string;
  params?: Record<string, unknown>;
  fields?: ProblemField[];
  trace_id?: string;
};
