/**
 * Numbers behind the interactive charts. They come from marketing/business-model/model/cost_model.py
 * (prices checked 23–24 September 2026); rerun that model and update these together.
 */

export type Pipeline = "promo" | "list" | "optimised";

export const pipelineLabels: Record<Pipeline, string> = {
  promo: "Today (2026 prices)",
  list: "From Jan 2027",
  optimised: "Cheaper pipeline",
};

export type LessonStep = { id: string; name: string; tokens: string; model: Record<Pipeline, string>; cost: Record<Pipeline, number> };

export const lessonSteps: LessonStep[] = [
  {
    id: "moderation", name: "Moderation", tokens: "one image",
    model: { promo: "omni-moderation", list: "omni-moderation", optimised: "omni-moderation" },
    cost: { promo: 0, list: 0, optimised: 0 },
  },
  {
    id: "scene", name: "Scene analysis", tokens: "3,920 in · 900 out",
    model: { promo: "gemini-3.7-flash", list: "gemini-3.7-flash", optimised: "gemini-3.1-flash-lite" },
    cost: { promo: 0.00695, list: 0.01389, optimised: 0.00241 },
  },
  {
    id: "translation", name: "Translation", tokens: "1,000 in · 500 out",
    model: { promo: "gemini-3.5-flash-lite", list: "gemini-3.5-flash-lite", optimised: "gemini-2.5-flash-lite" },
    cost: { promo: 0.00171, list: 0.00171, optimised: 0.00016 },
  },
  {
    id: "tasks", name: "Learning tasks", tokens: "3,000 in · 2,000 out",
    model: { promo: "gpt-4o-mini", list: "gpt-4o-mini", optimised: "gpt-4.1-nano" },
    cost: { promo: 0.00182, list: 0.00182, optimised: 0.00121 },
  },
  {
    id: "ispy", name: "I-Spy clues and feedback", tokens: "4,800 in · 1,050 out",
    model: { promo: "gpt-4o-mini", list: "gpt-4o-mini", optimised: "gpt-4.1-nano" },
    cost: { promo: 0.00148, list: 0.00148, optimised: 0.00099 },
  },
];

/** Blended monthly AI and storage cost per learner (free mix 50/35/15, Plus mix 80/20). */
export const learnerCost: Record<Pipeline, { free: number; plus: number; casual: number; cap: number; typical: number }> = {
  promo: { free: 0.109, plus: 0.678, casual: 0.11, cap: 0.39, typical: 0.49 },
  list: { free: 0.167, plus: 0.969, casual: 0.16, cap: 0.6, typical: 0.7 },
  optimised: { free: 0.049, plus: 0.373, casual: 0.05, cap: 0.17, typical: 0.27 },
};

/** Net monthly revenue per payer after Stripe fees, 59% annual ($49.99) and 41% monthly ($7.99). */
export const NET_ARPU = 5.2404;

export function fixedCost(monthlyUsers: number): number {
  return monthlyUsers > 10_000 ? 70 : 52;
}

export function monthlyResult(users: number, conversion: number, pipeline: Pipeline) {
  const payers = users * conversion;
  const revenue = payers * NET_ARPU;
  const ai = (users - payers) * learnerCost[pipeline].free + payers * learnerCost[pipeline].plus;
  const fixed = fixedCost(users);
  return { payers, revenue, ai, fixed, result: revenue - ai - fixed };
}

export function breakEvenConversion(users: number, pipeline: Pipeline): number {
  const { free, plus } = learnerCost[pipeline];
  // c·u·(arpu − plus) = (1 − c)·u·free + fixed
  return (users * free + fixedCost(users)) / (users * (NET_ARPU - plus + free));
}

export const usd = (value: number, digits = 0) =>
  `${value < 0 ? "−" : ""}$${Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
