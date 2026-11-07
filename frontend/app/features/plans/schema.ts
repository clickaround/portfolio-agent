// What the plan page reads from the book plan (editorial decisions only; never coordinates). The full contract is the backend's book-plan schema.
export type PlanPage = { role: string; assets?: string[]; section?: string; title?: string; tagline?: string; flags?: string[] };

export function planPages(plan: Record<string, unknown> | null): PlanPage[] {
  return plan && Array.isArray(plan.pages) ? (plan.pages as PlanPage[]) : [];
}
